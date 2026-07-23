"""Tests for POST /projects/{project_id}/ratings/."""
from rest_framework import status

from core.enums import ProjectStatus
from core.models import Bid, Project, Rating
from core.tests.helpers import AuthenticatedAPITestCase


class RatingFlowTests(AuthenticatedAPITestCase):
    def setUp(self):
        self.owner = self.create_and_login('client1', 'client')
        self.project = Project.objects.create(
            title='Landing page', description='Build one', budget=100,
            owner=self.owner,
        )
        self.freelancer = self.create_and_login('freelancer1', 'freelancer')
        self.bid = Bid.objects.create(
            price=90, message='pick me please', project=self.project,
            freelancer=self.freelancer,
        )

        # owner accepts the bid, then marks the project complete
        self.login_as(self.owner)
        self.client.patch(f'/projects/{self.project.id}/bids/{self.bid.id}/accept/')
        self.client.patch(f'/projects/{self.project.id}/complete/')
        self.project.refresh_from_db()

    def test_rating_requires_project_completed(self):
        in_progress_project = Project.objects.create(
            title='Another project', description='desc', budget=50,
            owner=self.owner, status=ProjectStatus.IN_PROGRESS,
            winner=self.freelancer,
        )
        res = self.client.post(
            f'/projects/{in_progress_project.id}/ratings/',
            {'score': 5, 'comment': 'great work'},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_can_rate_freelancer(self):
        res = self.client.post(
            f'/projects/{self.project.id}/ratings/',
            {'score': 5, 'comment': 'great work'},
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        rating = Rating.objects.get(project=self.project, from_user=self.owner)
        self.assertEqual(rating.to_user_id, self.freelancer.id)
        self.assertEqual(rating.score, 5)

    def test_freelancer_can_rate_owner(self):
        self.login_as(self.freelancer)
        res = self.client.post(
            f'/projects/{self.project.id}/ratings/',
            {'score': 4, 'comment': 'good client'},
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        rating = Rating.objects.get(project=self.project, from_user=self.freelancer)
        self.assertEqual(rating.to_user_id, self.owner.id)

    def test_cannot_rate_same_project_twice(self):
        self.client.post(
            f'/projects/{self.project.id}/ratings/',
            {'score': 5, 'comment': 'great work'},
        )
        res = self.client.post(
            f'/projects/{self.project.id}/ratings/',
            {'score': 3, 'comment': 'changed my mind'},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            Rating.objects.filter(project=self.project, from_user=self.owner).count(), 1
        )

    def test_stranger_cannot_rate_project(self):
        self.create_and_login('stranger1', 'freelancer')
        res = self.client.post(
            f'/projects/{self.project.id}/ratings/',
            {'score': 5, 'comment': 'not involved'},
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_score_out_of_range_is_rejected(self):
        res = self.client.post(
            f'/projects/{self.project.id}/ratings/',
            {'score': 11, 'comment': 'too high'},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
