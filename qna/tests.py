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


