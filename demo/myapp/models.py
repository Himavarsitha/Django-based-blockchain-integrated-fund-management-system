from django.db import models
from django.contrib.auth.models import User
# from django.utils.functional import cached_property
from django.db.models import Sum
import secrets
from web3 import Web3


class Organization(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="organization")
    name = models.CharField(max_length=255, unique=True)
    email = models.EmailField(unique=True)
    contact = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    wallet_address = models.CharField(max_length=42, blank=True, null=True)  # Ethereum wallet address

    def save(self, *args, **kwargs):
        if not self.wallet_address:
            self.wallet_address = self.generate_wallet_address()
        super().save(*args, **kwargs)

    def generate_wallet_address(self):
        raw_address = "0x" + secrets.token_hex(20)
        return Web3.to_checksum_address(raw_address)

    @property
    def available_funds(self):
        total_funds = self.transactions.filter(transaction_type="Credit").aggregate(Sum("amount"))["amount__sum"] or 0
        total_debits = self.transactions.filter(transaction_type="Debit").aggregate(Sum("amount"))["amount__sum"] or 0
        return total_funds - total_debits


    def __str__(self):
        return f"{self.name} ({self.user.username})"


class FundRequest(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="fund_requests")
    amount_requested = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_requests",
        limit_choices_to={'is_staff': True}
    )
    rejection_reason = models.TextField(blank=True, null=True)
    blockchain_reference = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Request {self.id} - {self.organization.name} - {self.status}"


class StateGovernment(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="state_government")
    department_name = models.CharField(max_length=255)

    def __str__(self):
        return self.department_name


class Fund(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    allocated_to = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="funds")
    allocated_at = models.DateTimeField(auto_now_add=True)
    blockchain_id = models.CharField(max_length=255, unique=True, null=True, blank=True)

    def __str__(self):
        return f"{self.amount} allocated to {self.allocated_to.name}"


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('Credit', 'Credit'),
        ('Debit', 'Debit'),
    ]

    fund_request = models.ForeignKey(FundRequest, on_delete=models.CASCADE, null=True, blank=True, related_name="transactions")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="transactions")
    fund = models.ForeignKey(Fund, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    transaction_hash = models.CharField(max_length=100, unique=True, null=True, blank=True)
    wallet_address = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.transaction_type} of {self.amount} for {self.organization.name}"


class UserFundRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} → {self.organization.name} | ₹{self.amount} | {self.status}"
