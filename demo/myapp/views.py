from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum
from django.http import JsonResponse
from django.db import transaction as db_transaction
from .models import Organization, Transaction, FundRequest, Fund, StateGovernment, UserFundRequest
from .forms import FundRequestForm, FundApprovalForm, UserSignupForm, UserLoginForm, UserFundRequestForm
from blockchain.blockchain import send_transaction, get_transaction_status,inr_to_eth
from web3 import Web3
import os

# ============== GENERAL AUTH & HOME ==============

def home(request):
    return render(request, "home.html")

def login_view(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")

            if user.is_staff:
                return redirect("state_dashboard")

            try:
                if hasattr(user, 'organization'):
                    return redirect("dashboard")
            except:
                pass

            return redirect("user_dashboard")
        else:
            messages.error(request, "Invalid email or password.")
    return render(request, "login.html")

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("login")

# ============== ORGANIZATION SIGNUP & DASHBOARD ==============

def organization_signup(request):
    if request.method == "POST":
        username = request.POST["email"]
        email = request.POST["email"]
        password = request.POST["password"]
        org_name = request.POST.get("name", "").strip()

        if not org_name:
            messages.error(request, "Organization name is required.")
            return redirect("organization_signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "User already exists.")
            return redirect("organization_signup")

        user = User.objects.create_user(username=username, email=email, password=password)
        Organization.objects.create(user=user, name=org_name, email=email)
        login(request, user)
        return redirect("dashboard")

    return render(request, "organization_signup.html")

@login_required
def organization_dashboard(request):
    try:
        organization = request.user.organization
    except Organization.DoesNotExist:
        return render(request, "error.html", {"message": "You are not linked to any organization."})

    transactions = Transaction.objects.filter(organization=organization)
    fund_requests = FundRequest.objects.filter(organization=organization).order_by("-requested_at")
    user_fund_requests = UserFundRequest.objects.filter(organization=organization).order_by("-created_at")

    context = {
        "organization": organization,
        "transactions": transactions,
        "fund_requests": fund_requests,
        "user_fund_requests": user_fund_requests
    }
    return render(request, "organization_dashboard.html", context)

@login_required
def request_funds(request):
    if request.user.is_staff or not hasattr(request.user, 'organization'):
        messages.error(request, "Only organizations can request funds.")
        return redirect("dashboard")

    if request.method == "POST":
        form = FundRequestForm(request.POST)
        if form.is_valid():
            fund_request = form.save(commit=False)
            fund_request.organization = request.user.organization
            fund_request.status = "PENDING"
            fund_request.save()
            messages.success(request, "Fund request submitted successfully!")
            return redirect("dashboard")
    else:
        form = FundRequestForm()

    return render(request, "request_funds.html", {"form": form})

# ============== GOVERNMENT SIGNUP & DASHBOARD ==============

def government_signup(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]
        department = request.POST.get("department", "").strip()

        if not department:
            messages.error(request, "Department is required.")
            return redirect("government_signup")

        if User.objects.filter(username=email).exists():
            messages.error(request, "User already exists.")
            return redirect("government_signup")

        user = User.objects.create_user(username=email, email=email, password=password, is_staff=True)
        StateGovernment.objects.create(user=user, department_name=department)
        login(request, user)
        return redirect("state_dashboard")

    return render(request, "government_signup.html")

'''@login_required
def state_government_dashboard(request):
    if not request.user.is_staff:
        return render(request, "error.html", {"message": "Unauthorized access"})

    organizations = Organization.objects.all()
    transactions = Transaction.objects.all()
    fund_requests = FundRequest.objects.filter(status="PENDING").order_by("-requested_at")

    context = {
        "organizations": organizations,
        "transactions": transactions,
        "fund_requests": fund_requests
    }
    return render(request, "state_government_dashboard.html", context)'''

@login_required
def state_government_dashboard(request):
    if not request.user.is_staff:
        return render(request, "error.html", {"message": "Unauthorized access"})

    # Get all data
    organizations = Organization.objects.all()
    fund_requests = FundRequest.objects.all().order_by("-requested_at")
    transactions = Transaction.objects.select_related('organization').all().order_by("-timestamp")

    # Key Metrics
    total_allocated_funds = Fund.objects.aggregate(total=Sum("amount"))["total"] or 0
    total_requests = fund_requests.count()
    pending_requests = fund_requests.filter(status="PENDING").count()
    approved_requests = fund_requests.filter(status="APPROVED").count()
    rejected_requests = fund_requests.filter(status="REJECTED").count()

    # Funds allocated to each organization
    org_fund_data = (
        Fund.objects.values("allocated_to__name")
        .annotate(total_funds=Sum("amount"))
        .order_by("-total_funds")
    )

    # Transaction summaries
    total_transactions = transactions.count()
    total_credited = transactions.filter(transaction_type="Credit").aggregate(Sum("amount"))["amount__sum"] or 0
    total_debited = transactions.filter(transaction_type="Debit").aggregate(Sum("amount"))["amount__sum"] or 0

    fund_usage_data = []
    for org in Organization.objects.all():
        allocated = Fund.objects.filter(allocated_to=org).aggregate(total=Sum("amount"))["total"] or 0
        used = Transaction.objects.filter(organization=org, transaction_type='Debit').aggregate(total=Sum("amount"))["total"] or 0
        remaining = allocated - used
        fund_usage_data.append({
            "organization": org.name,
            "allocated": allocated,
            "used": used,
            "remaining": remaining
        })

    context = {
        "organizations": organizations,
        "fund_requests": fund_requests[:10],  # Recent 10
        "transactions": transactions[:10],    # Recent 10

        # KPIs
        "total_allocated_funds": total_allocated_funds,
        "total_requests": total_requests,
        "pending_requests": pending_requests,
        "approved_requests": approved_requests,
        "rejected_requests": rejected_requests,
        "total_transactions": total_transactions,
        "total_credited": total_credited,
        "total_debited": total_debited,
        "org_fund_data": org_fund_data,
        "fund_usage_data": fund_usage_data,
    }

    return render(request, "state_government_dashboard.html", context)

# ============== FUND APPROVAL & BLOCKCHAIN ==============
from .forms import FundApprovalForm
@login_required
def review_fund_requests(request, request_id):
    if not request.user.is_staff:
        messages.error(request, "Unauthorized access.")
        return redirect("state_dashboard")

    fund_request = get_object_or_404(FundRequest, id=request_id)

    if fund_request.status in ["APPROVED", "REJECTED"]:
        return render(request, "review_fund_requests.html", {
            "fund_request": fund_request,
            "form": FundApprovalForm(instance=fund_request)
        })

    if request.method == "POST":
        form = FundApprovalForm(request.POST, instance=fund_request)

        if form.is_valid():
            status = request.POST.get("status")
            fund_request = form.save(commit=False)
            fund_request.status = status.upper()

            if status.upper() == "APPROVED":
                try:
                    with db_transaction.atomic():
                        approved_amount_inr= fund_request.amount_requested
                        eth_amount = inr_to_eth(approved_amount_inr)
                        print("💸 Converted ETH amount:", eth_amount)  # DEBUG
                        if eth_amount is None or float(eth_amount) <= 0:
                            messages.error(request, "⚠️ Conversion failed: invalid ETH amount.")
                            return redirect("review_fund_requests", request_id=fund_request.id)
                        eth_amount = float(eth_amount)

                        private_key = os.getenv("WALLET_PRIVATE_KEY")
                        public_key = Web3.to_checksum_address(os.getenv("WALLET_PUBLIC_KEY"))
                        org_wallet_address = Web3.to_checksum_address(fund_request.organization.wallet_address)

                        txn_hash = send_transaction(
                            from_address=public_key,
                            to_address=org_wallet_address,
                            amount_in_ether=eth_amount,
                            private_key=private_key
                        )

                        if not txn_hash:
                            raise Exception("Blockchain transaction failed.")

                        fund = Fund.objects.create(
                            allocated_to=fund_request.organization,
                            amount=fund_request.amount_requested
                        )

                        Transaction.objects.create(
                            organization=fund_request.organization,
                            amount=fund_request.amount_requested,
                            transaction_type="Credit",
                            description=f"Funds Approved: {fund_request.id}",
                            fund_request=fund_request,
                            transaction_hash=txn_hash,
                            fund=fund
                        )

                        fund_request.blockchain_reference = txn_hash
                        # Set reviewed_by
                        fund_request.reviewed_by = request.user
                        fund_request.status = "APPROVED"
                        fund_request.save()
                        messages.success(request, f"✅ Fund request {fund_request.id} approved and recorded on blockchain.")

                except Exception as e:
                    # db_transaction.set_rollback(True)
                    messages.error(request, f"❌ Blockchain transaction failed: {str(e)}")

            elif status.upper() == "REJECTED":
                # 💡 Set rejection reason from form
                rejection_reason = form.cleaned_data.get("rejection_reason")
                fund_request.rejection_reason = rejection_reason

                # 💡 Set reviewer and status
                fund_request.reviewed_by = request.user
                fund_request.status = "REJECTED"
                fund_request.save()
                messages.info(request, f"❌ Fund request {fund_request.id} has been rejected.")

            return redirect("review_fund_requests", request_id=fund_request.id)
    else:
        form = FundApprovalForm(instance=fund_request)

    return render(request, "review_fund_requests.html", {
        "fund_request": fund_request,
        "form": form
    })

@login_required
def get_transaction_details(request, txn_hash):
    try:
        if not txn_hash or len(txn_hash) != 66:
            raise ValueError("Invalid transaction hash format.")

        txn_details = get_transaction_status(txn_hash)
        return JsonResponse({"status": "success", "transaction": txn_details})
    except ValueError as ve:
        return JsonResponse({"status": "error", "message": str(ve)}, status=400)
    except Exception:
        return JsonResponse({"status": "error", "message": "Failed to fetch transaction details."}, status=500)

# ============== USER SIGNUP, LOGIN & FUND REQUEST ==============

def user_signup(request):
    if request.method == 'POST':
        form = UserSignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            return redirect('user_dashboard')
    else:
        form = UserSignupForm()
    return render(request, 'user_signup.html', {'form': form})

def user_login_view(request):
    error = None
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('user_dashboard')
            else:
                error = "Incorrect email or password."
    else:
        form = UserLoginForm()
    return render(request, 'user_login.html', {'form': form, 'error': error})

@login_required
def user_dashboard(request):
    requests = UserFundRequest.objects.filter(user=request.user)
    return render(request, 'user_dashboard.html', {'requests': requests})

@login_required
def fund_request(request):
    if request.method == 'POST':
        form = UserFundRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.user = request.user
            req.save()
            return redirect('user_dashboard')
    else:
        form = UserFundRequestForm()
    return render(request, 'fund_request_user.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('user_login')

# ============== APPROVE/REJECT USER FUND REQUESTS ==============

@login_required
def approve_or_reject_user_fund(request, request_id, action):
    if not hasattr(request.user, 'organization'):
        messages.error(request, "Unauthorized access.")
        return redirect("dashboard")

    org = request.user.organization
    user_fund_request = get_object_or_404(UserFundRequest, id=request_id, organization=org)
    print("Org funds:", org.available_funds)
    print("Request amount:", user_fund_request.amount)
    print("Org funds type:", type(org.available_funds))
    print("Request amount type:", type(user_fund_request.amount))

    if user_fund_request.status != "Pending":
        messages.warning(request, f"Request already {user_fund_request.status}.")
        return redirect("dashboard")

    if action == "Approved":
        if org.available_funds < user_fund_request.amount:
            messages.error(request, "Insufficient funds in the organization wallet.")
            return redirect("dashboard")

        user_fund_request.status = "Approved"
        # org.available_funds -= user_fund_request.amount  # 🛠️ Deduct the amount
        org.save()  # 🛠️ Save updated fund
        user_fund_request.save()

        Transaction.objects.create(
            organization=org,
            amount=user_fund_request.amount,
            transaction_type="Debit",
            description=f"User Fund Approved (Request ID: {user_fund_request.id})"
        )

        messages.success(request, f"User fund request {user_fund_request.id} approved.")

    elif action == "Rejected":
        user_fund_request.status = "Rejected"
        user_fund_request.save()
        messages.info(request, f"User fund request {user_fund_request.id} rejected.")
    else:
        messages.error(request, "Invalid action.")
        return redirect("dashboard")

    return redirect("dashboard")
