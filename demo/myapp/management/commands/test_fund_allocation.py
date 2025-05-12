from django.core.management.base import BaseCommand
from decimal import Decimal
from myapp.models import FundRequest, Organization
from blockchain.blockchain import allocate_funds_on_blockchain, send_transaction, get_transaction_status
from django.utils import timezone
import random

class Command(BaseCommand):
    help = "Test blockchain fund allocation using a sample fund request"

    def handle(self, *args, **kwargs):
        try:
            # Create a sample organization if not exists
            org, created = Organization.objects.get_or_create(
                name="new organization",
                defaults={"wallet_address": "0x228dC3fF59d1D585e61Ca9412264254A3eB9A470"}
            )
            if created:
                self.stdout.write(self.style.SUCCESS("✅ Created test organization"))

            # Create a sample fund request
            request = FundRequest.objects.create(
                organization=org,
                amount_requested=Decimal("100.00"),  # ₹100
                reason="Testing fund allocation",
                status="approved"
            )
            self.stdout.write(self.style.SUCCESS(f"✅ Created FundRequest with ID {request.id}"))

            # Allocate funds on blockchain
            self.stdout.write("⏳ Allocating on blockchain...")
            tx_hash = allocate_funds_on_blockchain(request.id)

            if tx_hash:
                status = get_transaction_status(tx_hash)
                self.stdout.write(self.style.SUCCESS(f"✅ Tx Hash: {tx_hash}"))
                self.stdout.write(self.style.SUCCESS(f"📦 Status: {status}"))
            else:
                self.stdout.write(self.style.ERROR("❌ Blockchain allocation failed"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {str(e)}"))
