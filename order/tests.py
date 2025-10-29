from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Order, OrderItem
from asset.models import Asset


class OrderModelTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='testuser', password='pass1234')
        self.asset = Asset.objects.create(name='Test Asset', price=100)

    def test_dc_number_autogenerates_on_save(self):
        order = Order.objects.create(user=self.user, order_id='ORD1', amount=100)
        self.assertTrue(order.dc_number.startswith('DC'))
        self.assertEqual(len(order.dc_number), 6)  # e.g., DC0001

    def test_total_items_and_total_amount_methods(self):
        order = Order.objects.create(user=self.user, order_id='ORD2', amount=0)
        OrderItem.objects.create(order=order, asset=self.asset, quantity=2, price=50)
        OrderItem.objects.create(order=order, asset=self.asset, quantity=1, price=25)
        self.assertEqual(order.total_items(), 2)
        self.assertEqual(order.total_amount(), 125)


class OrderViewsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass1234')
        self.other = User.objects.create_user(username='other', password='pass1234')
        self.asset = Asset.objects.create(name='Test Asset', price=100)
        self.order = Order.objects.create(user=self.user, order_id='ORD100', amount=150)
        self.item = OrderItem.objects.create(order=self.order, asset=self.asset, quantity=3, price=50)

    def test_orders_list_requires_login(self):
        url = reverse('orders_list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/accounts/login', resp['Location'])

    def test_orders_list_shows_only_user_orders(self):
        self.client.login(username='testuser', password='pass1234')
        # create other user's order
        Order.objects.create(user=self.other, order_id='ORD200', amount=10)
        url = reverse('orders_list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        orders = resp.context['orders']
        self.assertEqual(list(orders), [self.order])

    def test_order_detail_only_owner_access(self):
        self.client.login(username='testuser', password='pass1234')
        url = reverse('order_detail', kwargs={"pk": self.order.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # other user should get 404
        self.client.logout()
        self.client.login(username='other', password='pass1234')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_mark_order_received_success(self):
        url = reverse('mark_order_received', kwargs={"order_id": self.order.pk})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.shipping_status, 2)

    def test_mark_order_received_not_found(self):
        url = reverse('mark_order_received', kwargs={"order_id": 999999})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        self.assertJSONEqual(resp.content, {"success": False, "message": "Order not found."})
