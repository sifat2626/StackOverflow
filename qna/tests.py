from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Tags


class TagPermissionsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.regular_user = User.objects.create_user(username='regular', password='password123')
        self.admin_user = User.objects.create_superuser(username='admin', password='password123')
        self.tag = Tags.objects.create(name='python')

    def test_unauthenticated_cannot_create_tag(self):
        response = self.client.post(
            reverse('tag-list'),
            data={'name': 'django'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
        self.assertFalse(Tags.objects.filter(name='django').exists())

    def test_regular_user_cannot_create_tag(self):
        self.client.login(username='regular', password='password123')
        response = self.client.post(
            reverse('tag-list'),
            data={'name': 'django'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Tags.objects.filter(name='django').exists())

    def test_admin_can_create_tag(self):
        self.client.login(username='admin', password='password123')
        response = self.client.post(
            reverse('tag-list'),
            data={'name': 'django'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Tags.objects.filter(name='django').exists())

    def test_regular_user_cannot_delete_tag(self):
        self.client.login(username='regular', password='password123')
        response = self.client.delete(reverse('tag-detail', kwargs={'pk': self.tag.id}))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Tags.objects.filter(id=self.tag.id).exists())

    def test_admin_can_delete_tag(self):
        self.client.login(username='admin', password='password123')
        response = self.client.delete(reverse('tag-detail', kwargs={'pk': self.tag.id}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Tags.objects.filter(id=self.tag.id).exists())

    def test_regular_user_cannot_update_tag(self):
        self.client.login(username='regular', password='password123')
        response = self.client.put(
            reverse('tag-detail', kwargs={'pk': self.tag.id}),
            data={'name': 'python3'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_can_update_tag(self):
        self.client.login(username='admin', password='password123')
        response = self.client.put(
            reverse('tag-detail', kwargs={'pk': self.tag.id}),
            data={'name': 'python3'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.tag.refresh_from_db()
        self.assertEqual(self.tag.name, 'python3')

    def test_admin_update_tag_with_same_name_succeeds(self):
        self.client.login(username='admin', password='password123')
        response = self.client.put(
            reverse('tag-detail', kwargs={'pk': self.tag.id}),
            data={'name': 'python'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)


class QuestionListViewTestCase(TestCase):
    def setUp(self):
        from userprofile.models import UserProfile
        from qna.models import Question, Answer
        self.user_obj = User.objects.create_user(username='author1', password='password123')
        self.profile = UserProfile.objects.create(user=self.user_obj)
        self.tag1 = Tags.objects.create(name='python')
        self.tag2 = Tags.objects.create(name='django')

        # Create multiple questions with tags and answers to test N+1 query performance
        for i in range(5):
            q = Question.objects.create(
                title=f'Question {i}',
                description=f'Description {i}',
                created_by=self.profile
            )
            q.tags.add(self.tag1, self.tag2)
            Answer.objects.create(question=q, answer=f'Answer {i}', created_by=self.profile)

    def test_get_questions_list_query_count_and_data(self):
        from django.db import connection
        from django.test import utils

        with self.assertNumQueries(2):
            response = self.client.get(reverse('question-list'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('questions', data)
        questions = data['questions']
        self.assertEqual(len(questions), 5)
        
        # Verify fields on serialized output
        first_q = questions[0]
        self.assertIn('title', first_q)
        self.assertEqual(first_q['created_by'], 'author1')
        self.assertCountEqual(first_q['tags'], ['python', 'django'])
        self.assertEqual(first_q['answers_count'], 1)


class AnswerVoteTestCase(TestCase):
    def setUp(self):
        from userprofile.models import UserProfile
        from qna.models import Question, Answer
        self.author_user = User.objects.create_user(username='answer_author', password='password123')
        self.author_profile = UserProfile.objects.create(user=self.author_user, reputation=0)

        self.voter_user = User.objects.create_user(username='voter', password='password123')
        self.voter_profile = UserProfile.objects.create(user=self.voter_user, reputation=0)

        self.question = Question.objects.create(
            title='Sample Q',
            description='Sample Desc',
            created_by=self.author_profile
        )
        self.answer = Answer.objects.create(
            question=self.question,
            answer='Sample Ans',
            created_by=self.author_profile
        )

    def test_voting_uses_f_expression_and_updates_reputation(self):
        from django.db import connection, reset_queries
        from django.test import override_settings
        self.client.login(username='voter', password='password123')
        
        with override_settings(DEBUG=True):
            reset_queries()
            response = self.client.post(
                reverse('answer-vote', kwargs={'pk': self.answer.id}),
                data={'vote': 'up'},
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)

            # Inspect captured SQL queries to verify F() update expression was executed
            sql_statements = [q['sql'] for q in connection.queries]
            f_expression_used = any('UPDATE' in sql.upper() and 'reputation' in sql.lower() for sql in sql_statements)
            self.assertTrue(f_expression_used, f"Expected SQL query updating reputation using F() expression. Queries: {sql_statements}")

        self.author_profile.refresh_from_db()
        self.assertEqual(self.author_profile.reputation, 10)

        self.answer.refresh_from_db()
        self.assertEqual(self.answer.upvote_count, 1)


class AcceptAnswerTestCase(TestCase):
    def setUp(self):
        from userprofile.models import UserProfile
        from qna.models import Question, Answer
        self.q_author = User.objects.create_user(username='q_author', password='password123')
        self.q_author_profile = UserProfile.objects.create(user=self.q_author)

        self.ans_author1 = User.objects.create_user(username='ans_author1', password='password123')
        self.ans_profile1 = UserProfile.objects.create(user=self.ans_author1, reputation=0)

        self.ans_author2 = User.objects.create_user(username='ans_author2', password='password123')
        self.ans_profile2 = UserProfile.objects.create(user=self.ans_author2, reputation=0)

        self.question = Question.objects.create(
            title='Question to accept',
            description='Desc',
            created_by=self.q_author_profile
        )

        self.answer1 = Answer.objects.create(
            question=self.question,
            answer='Ans 1',
            created_by=self.ans_profile1
        )
        self.answer2 = Answer.objects.create(
            question=self.question,
            answer='Ans 2',
            created_by=self.ans_profile2
        )

    def test_non_author_cannot_accept_answer(self):
        self.client.login(username='ans_author1', password='password123')
        response = self.client.post(reverse('answer-accept', kwargs={'pk': self.answer1.id}))
        self.assertEqual(response.status_code, 403)

    def test_author_accept_answer_atomic_success(self):
        self.client.login(username='q_author', password='password123')
        response = self.client.post(reverse('answer-accept', kwargs={'pk': self.answer1.id}))
        self.assertEqual(response.status_code, 200)

        self.question.refresh_from_db()
        self.assertEqual(self.question.accepted_answer_id, self.answer1.id)

        self.ans_profile1.refresh_from_db()
        self.assertEqual(self.ans_profile1.reputation, 15)

    def test_author_switch_accepted_answer_atomic_success(self):
        self.client.login(username='q_author', password='password123')
        # Accept answer 1 first
        self.client.post(reverse('answer-accept', kwargs={'pk': self.answer1.id}))
        
        # Switch to accept answer 2
        response = self.client.post(reverse('answer-accept', kwargs={'pk': self.answer2.id}))
        self.assertEqual(response.status_code, 200)

        self.question.refresh_from_db()
        self.assertEqual(self.question.accepted_answer_id, self.answer2.id)

        self.ans_profile1.refresh_from_db()
        self.ans_profile2.refresh_from_db()
        self.assertEqual(self.ans_profile1.reputation, 0)
        self.assertEqual(self.ans_profile2.reputation, 15)

    def test_atomic_rollback_on_failure(self):
        from unittest.mock import patch
        self.client.login(username='q_author', password='password123')

        # Simulate exception inside atomic block during reputation update
        with patch('userprofile.models.UserProfile.objects.filter', side_effect=Exception('Database error forced')):
            with self.assertRaises(Exception):
                self.client.post(reverse('answer-accept', kwargs={'pk': self.answer1.id}))

        self.question.refresh_from_db()
        self.assertIsNone(self.question.accepted_answer_id)
        self.ans_profile1.refresh_from_db()
        self.assertEqual(self.ans_profile1.reputation, 0)




