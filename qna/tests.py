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



