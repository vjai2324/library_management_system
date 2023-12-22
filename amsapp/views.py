import random
import requests
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import *
from .models import *
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db import IntegrityError
from datetime import datetime
from django.utils import timezone  # Import timezone
from datetime import timedelta  # Import timedelta
from django.views.decorators.http import require_GET, require_POST
from reportlab.pdfgen import canvas
from django.http import HttpResponse, JsonResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from django.db.models import Q
import json
from webpush import send_user_notification
# from .filters import PurchaseFilter
from django.db.models import Max, Subquery, OuterRef
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from django.db import models


# Define API Key (consider using environment variables for security)
GOOGLE_BOOKS_API_KEY = 'AIzaSyAew238ORgqCNbNyb0PdeF6eay4Rc54Ls4'  # Replace with your API key
query = 'all books'


# Utility function to fetch book details from the Google Books API
# def fetch_book_details_from_api(book_id):
#     try:
#         endpoint = f'https://www.googleapis.com/books/v1/volumes/{book_id}?key={GOOGLE_BOOKS_API_KEY}'
#         response = requests.get(endpoint)
#
#         if response.status_code == 200:
#             return response.json()
#         else:
#             return None
#     except requests.exceptions.RequestException as e:
#         print(f"An error occurred during the API request: {str(e)}")
#         return None

# List of random search keywords or phrases
random_search_keywords = ["science fiction", "history", "cooking", "mystery", "biography","computer science","Comics & Graphic Novels"]

# Generate a random search query from the list
random_query = random.choice(random_search_keywords)

def index(request):
    # Subquery to get the maximum popularity for each distinct title
    max_popularity_subquery = Book.objects.filter(title=OuterRef('title')).values('title').annotate(max_popularity=Max('popularity')).values('max_popularity')

    # Retrieve the most popular books based on the distinct titles and their maximum popularity
    popular_books = Book.objects.filter(
        popularity=Subquery(max_popularity_subquery)
    ).order_by('-popularity')[:6]

    return render(request, 'index.html', {'popular_books': popular_books})


def getdata(request):
    # Initial data retrieval, e.g., when page loads
    api_url = f'https://www.googleapis.com/books/v1/volumes?q={random_query}&orderBy=newest&startIndex=0&maxResults=40&key={GOOGLE_BOOKS_API_KEY}'
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        return render(request, 'getdata.html', {'data': data})
    else:
        error_message = 'Failed to fetch data from the API'
        return render(request, '404.html', {'error_message': error_message})

current_offset = 0  # Initialize the offset

def fetch_more_data(request):
    global current_offset

    try:
        # Increment the current offset for each request
        current_offset += 1
        start_index = current_offset * 40  # Adjust as needed based on your pagination logic
        api_url = f'https://www.googleapis.com/books/v1/volumes?q={random_query}&orderBy=newest&startIndex={start_index}&maxResults=40&key={GOOGLE_BOOKS_API_KEY}'
        
        response = requests.get(api_url)

        if response.status_code == 200:
            data = response.json()
            return JsonResponse({'data': data})
        else:
            error_message = f'Failed to fetch data. Status code: {response.status_code}'
            # You can log this error message for debugging
            print(error_message)
            return JsonResponse({'error': error_message}, status=500)
    except Exception as e:
        # Handle exceptions and log them
        error_message = f'An error occurred: {str(e)}'
        print(error_message)
        return JsonResponse({'error': error_message}, status=500)

def book_search(request):
    if request.method == 'GET':
        form = BookSearchForm(request.GET)

        # Retrieve available categories from Google Books API
        categories_api_url = "https://www.googleapis.com/books/v1/volumes?key={}&q=".format(GOOGLE_BOOKS_API_KEY)
        categories_api_url += "inauthor:none&maxResults=40"  # Request a single result to get categories

        categories_response = requests.get(categories_api_url)
        categories_data = categories_response.json()

        # Extract available categories from the response
        available_categories = []
        for item in categories_data.get('items', []):
            categories = item.get('volumeInfo', {}).get('categories', [])
            available_categories.extend(categories)

        # Remove duplicates and sort the categories alphabetically
        available_categories = sorted(set(available_categories))

        # Add available categories to the form's category field choices
        form.fields['category'].choices = [('', 'All Categories')] + [(category, category) for category in available_categories]

        if form.is_valid():
            cleaned_data = form.cleaned_data
            query = cleaned_data.get('query')
            category = cleaned_data.get('category')
            author = cleaned_data.get('author')
            publication_year = cleaned_data.get('publication_year')

            api_url = "https://www.googleapis.com/books/v1/volumes?key={}&maxResults=40&q=".format(GOOGLE_BOOKS_API_KEY)

            if query:
                api_url += f"{query}&"
            if category:
                api_url += f"subject:{category}&"
            if author:
                api_url += f"inauthor:{author}&"
            if publication_year:
                api_url += f"publishedDate:{publication_year}&"

            response = requests.get(api_url)
            data = response.json()
            return render(request, 'book_search.html', {'data': data, 'form': form})
    else:
        form = BookSearchForm()

    return render(request, 'book_search.html', {'form': form})


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        p_reg_form = ProfileRegisterForm(request.POST)
        if form.is_valid() and p_reg_form.is_valid():
            user = form.save()
            p_data = p_reg_form.cleaned_data  # Get profile form data

            # Create the user's profile and set the pincode, district, and state
            profile = Profile.objects.create(user=user, **p_data)

            messages.success(request, 'Your account has been sent for approval!')
            login(request, user)  # Automatically log in the user
            return redirect('login')
        else:
            messages.error(request, 'Registration failed. Please check your data.')

    else:
        form = UserRegisterForm()
        p_reg_form = ProfileRegisterForm()

    context = {
        'form': form,
        'p_reg_form': p_reg_form
    }
    return render(request, 'register.html', context)


def loginform(request):
    # Check if the user is already authenticated; if yes, redirect them to another page (e.g., index).
    if request.user.is_authenticated:
        return redirect('index')  # Replace 'index' with your desired URL name

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f'Hi {username.title()}, welcome back!')
                return redirect('index')  # Redirect to the index page or another page
            else:
                messages.error(request, 'Invalid username or password')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})  # Replace 'login.html' with your login template path

@login_required
def sign_out(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')


@login_required
def add_to_cart(request, book_id):
    try:
        api_url = f'https://www.googleapis.com/books/v1/volumes/{book_id}?key={GOOGLE_BOOKS_API_KEY}'
        response = requests.get(api_url)

        if response.status_code == 200:
            data = response.json()
            volume_info = data.get('volumeInfo', {})
            book_id = data.get('id', '')

            # Create a new GoogleBook instance
            google_book = GoogleBook(
                title=volume_info.get('title', ''),
                author=', '.join(volume_info.get('authors', [])),
                category=', '.join(volume_info.get('categories', [])),
                published_date=volume_info.get('publishedDate', ''),
                description=volume_info.get('description', ''),
                book_id=book_id,
            )
            google_book.save()

            # Create a new Book instance
            direct_book = Book(
                title=volume_info.get('title', ''),
                author=', '.join(volume_info.get('authors', [])),
                category=', '.join(volume_info.get('categories', [])),
                publication_date=volume_info.get('publishedDate', ''),
                description=volume_info.get('description', ''),
                book_id=book_id,
                cover_image=volume_info.get('imageLinks', {}).get('thumbnail', ''),
            )
            direct_book.save()

        else:
            # Handle API response errors
            messages.error(request, f'Google Books API returned status code {response.status_code}')
            return redirect('cart')  # Redirect to the cart or an appropriate page

        # Check if the book with the given book_id exists
        books = Book.objects.filter(book_id=book_id)
        if books.exists():
            # Get the first matching book
            book = books.first()

            # Update popularity when a book is added to the cart
            book.popularity += 1
            book.save()

            # Get or create the cart for the current user
            cart, created = Cart.objects.get_or_create(user=request.user)

            if book not in cart.items.all():
                cart.items.add(book)
            return redirect('cart')
        else:
            messages.error(request, 'Book not found in the database.')
            return redirect('cart')  # Redirect to the cart or an appropriate page

    except requests.RequestException as e:
        # Handle network-related errors
        messages.error(request, f'Failed to connect to Google Books API: {e}')
        return redirect('cart')  # Redirect to the cart or an appropriate page

    except ValueError as e:
        # Handle JSON parsing errors
        messages.error(request, f'Failed to parse JSON response from Google Books API: {e}')
        return redirect('cart')  # Redirect to the cart or an appropriate page

    except IntegrityError as e:
        # Handle database integrity errors
        messages.error(request, f'Database error: {e}')
        return redirect('cart')  # Redirect to the cart or an appropriate page

    except MultipleObjectsReturned:
        # Handle the case where multiple books with the same book_id exist
        # You can choose to return the first matching book or handle it differently
        books = Book.objects.filter(book_id=book_id)
        book = books.first()  # Get the first matching book
        # Or handle it differently based on your application logic
        error_message = 'Multiple books with the same ID found.'

    messages.error(request, error_message)
    return redirect('cart')

@login_required
def cart(request):
    if request.method == 'POST':
        user = request.user
        book_id = request.POST.get('book_id')
        request_message = request.POST.get('request_message')
        try:
            date_from = datetime.strptime(request.POST.get('date_from'), '%Y-%m-%d').date()
            date_to = datetime.strptime(request.POST.get('date_to'), '%Y-%m-%d').date()
        except ValueError:
            # Handle date parsing error
            messages.error(request, 'Invalid date format. Please use YYYY-MM-DD format.')
            return redirect('cart')

        # Create a request instance for the selected book
        book = get_object_or_404(Book, id=book_id)
       
        request_instance = BookAvailabilityRequest.objects.create(
            user=user,
            book=book,
            status='pending',
            message=request_message,
            date_from=date_from,
            date_to=date_to
        )
        request_instance.save()


        # Optionally, you can add a success message
        messages.success(request, 'Request sent successfully.')

        return redirect('cart')  # Redirect to the cart page

    if request.user.is_superuser:
        # For superusers, display all books
        book_items = Book.objects.all()
    else:
        # For regular users, display their cart items
        user = request.user
        cart, created = Cart.objects.get_or_create(user=user)
        book_items = cart.items.all()



    # Initialize filters to None
    author_filter = request.GET.get('author')
    category_filter = request.GET.get('category')

    # Apply filters if criteria are provided
    if author_filter:
        book_items = book_items.filter(author__icontains=author_filter)

    if category_filter:
        book_items = book_items.filter(category__icontains=category_filter)

        # Calculate the date difference for each book with 'approved' status




    return render(request, 'cart.html', {'cart': book_items})

def password_reset(request):
    # Implement your password reset logic here
    return render(request, 'password_reset_form.html')


@login_required
def submit_request(request):
    if request.method == 'POST':
        user = request.user
        book_id = request.POST['book_id']
        book = Book.objects.get(id=book_id)

        # Create a new request instance with status set to 'pending'
        request_instance = BookAvailabilityRequest.objects.create(user=user, book=book, status='pending')
        request_instance.save()
        return redirect('user_requests')

    # Render a form for users to submit requests
    return render(request, 'submit_request.html')


@login_required
def review_requests(request):
    if not request.user.is_superuser:
        return redirect('index')

    pending_requests = BookAvailabilityRequest.objects.filter(status='pending')

    if request.method == 'POST':
        # Handle form submission for request approval or rejection
        request_id = request.POST.get('request_id')
        new_status = request.POST.get('new_status')

        if new_status in ('approved', 'rejected'):
            request_to_approve = BookAvailabilityRequest.objects.get(id=request_id)
            request_to_approve.status = new_status
            request_to_approve.save()

            # Optionally, you can add a success message
            messages.success(request, f'Request {request_id} has been {new_status}.')

    return render(request, 'review_requests.html', {'pending_requests': pending_requests})


def send_request(request):
    if request.method == 'POST':
        user = request.user
        book_ids = request.POST.getlist('book_ids')  # Get a list of selected book IDs
        request_message = request.POST.get('request_message')
        date_from = request.POST.get('date_from')  # Add this line
        date_to = request.POST.get('date_to')  # Add this line

        if not book_ids:
            messages.error(request, 'Please select at least one book to request.')
            return redirect('cart')  # Redirect back to the cart page

        # Create request instances for each selected book ID
        for book_id in book_ids:
            book = get_object_or_404(Book, id=book_id)

            # Check if the user has already requested this book
            existing_request = BookAvailabilityRequest.objects.filter(user=user, book_id=book_ids, status='pending').first()
            if existing_request:
                messages.warning(request, f'You have already requested "{book.title}".')
            else:
                request_instance = BookAvailabilityRequest.objects.create(
                    user=user,
                    book=book,
                    status='pending',
                    message=request_message,
                    date_from=date_from,  # Add this line
                    date_to=date_to,  # Add this line
                )
                request_instance.save()

        # Optionally, you can add a success message
        messages.success(request, 'Requests sent successfully.')

        return redirect('cart')  # Redirect to a page displaying user's requests

    # Render a form for users to submit requests
    return render(request, 'submit_request.html')

# def approve_all_pending_requests(request):
#     if not request.user.is_superuser:
#         # Optionally, you can add a permission check or other authentication logic here.
#         return redirect('index')  # Redirect non-superusers to the home page
#
#     # Approve all pending requests
#     pending_requests = BookAvailabilityRequest.objects.filter(status='pending')
#     for request in pending_requests:
#         request.status = 'approved'
#         request.save()
#
#     # Redirect to a page displaying a success message or other appropriate action
#     return redirect('review_requests')

@login_required
def approve_request(request, request_id):
    if not request.user.is_superuser:
        # Optionally, add a permission check or other authentication logic here.
        return redirect('index')  # Redirect non-superusers to the home page

    request_instance = get_object_or_404(BookAvailabilityRequest, id=request_id)

    if request_instance.status == 'pending':
        request_instance.status = 'approved'
        request_instance.save()

        # Update the status of the associated book
        book = request_instance.book
        book.status = 'approved'  # Set the status to 'approved' or your desired value
        book.save()

    return redirect('cart')  # Redirect back to the review page

@login_required
def reject_request(request, request_id):
    # Check if the user has permission to reject requests (e.g., superuser)
    if not request.user.is_superuser:
        # Optionally, add a permission check or other authentication logic here.
        return redirect('index')  # Redirect non-superusers to the home page or another appropriate view

    # Get the request instance with the specified request_id
    request_instance = get_object_or_404(BookAvailabilityRequest, id=request_id)

    if request_instance.status == 'pending':
        # Set the status of the request to 'rejected'
        request_instance.status = 'rejected'
        request_instance.save()

        # Optionally, you can add a success message
        messages.success(request, f'Request {request_id} has been rejected.')

    # Redirect back to the review page (e.g., 'review_requests')
    return redirect('cart')

@login_required
def user_details(request):
    if not request.user.is_superuser:
        # Optionally, you can add a permission check or other authentication logic here.
        return redirect('index')  # Redirect non-superusers to the home page or another appropriate view
    else:
        query = request.GET.get('query')
        users = User.objects.all()


    if query:
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )

    return render(request, 'user_details.html', {'users': users, 'query': query})




def issue_book(request, book_id):
    if not request.user.is_superuser:
        return redirect('access_denied')  # Create an "access_denied" view

    book = get_object_or_404(Book, id=book_id)

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        issue_date_str = request.POST.get('issue_date')
        return_date_str = request.POST.get('return_date')

        # Ensure the user exists
        user = get_object_or_404(User, id=user_id)

        # Parse the date strings to datetime objects
        issue_date = datetime.strptime(issue_date_str, '%Y-%m-%d')
        return_date = datetime.strptime(return_date_str, '%Y-%m-%d')

        # Create an IssuedBook instance
        issued_book = IssuedBook.objects.create(
            user=user,
            book=book,
            issue_date=issue_date,
            return_date=return_date
        )

        # Generate the bill and save it to the Bill table
        bill = generate_bill(user, book, issue_date, return_date)

        # Optionally, you can add a success message
        messages.success(request, 'Book issued successfully. Bill generated.')

        return redirect('cart')  # Redirect to the cart or another appropriate page

    # Retrieve a list of users (you may need to pass this data to the template)
    users = User.objects.all()

    return render(request, 'issue_book.html', {'book': book, 'users': users})



@login_required
def review_approved_requests(request):
    # Check if the user is a superuser
    if not request.user.is_superuser:
        # Optionally, you can add a permission check or other authentication logic here.
        return redirect('index')  # Redirect non-superusers to the home page or another appropriate view

    # Retrieve approved requests that are not yet issued
    approved_requests = BookAvailabilityRequest.objects.filter(status="approved", issuedbook__isnull=True)

    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        selected_user_id = request.POST.get('user_id')

        # Get the selected user and request instances
        selected_user = get_object_or_404(User, id=selected_user_id)
        request_instance = get_object_or_404(BookAvailabilityRequest, id=request_id)

        # Calculate issuance and due dates (customize this logic)
        issuance_date = timezone.now().date()
        due_date = issuance_date + timedelta(days=7)

        # Create an IssuedBook instance
        issued_book = IssuedBook.objects.create(
            user=selected_user,
            book=request_instance.book,
            issue_date=issuance_date,
            return_date=due_date
        )
        issued_book.save()

        # Calculate charges and create a bill
        charges = calculate_charges(selected_user, request_instance.book, issuance_date, due_date)
        bill = Bill.objects.create(
            user=selected_user,
            book=request_instance.book,
            issuance_date=issuance_date,
            due_date=due_date,
            charges=charges
        )
        bill.save()

        # Update the status of the request
        request_instance.status = 'issued'
        request_instance.save()

        # Optionally, you can add a success message
        messages.success(request, 'Book issued successfully. Bill generated.')

        return redirect('review_approved_requests')  # Redirect back to the review page

    return render(request, 'review_approved_requests.html', {'approved_requests': approved_requests})
def calculate_charges(user, book, issuance_date, due_date):
    # Calculate the number of days the book is rented
    rental_days = (due_date - issuance_date).days

    # Define the daily rate
    daily_rate = 10.0

    # Calculate total charges
    total_charges = daily_rate * rental_days

    return total_charges








def generate_bill(user, book, issue_date, return_date):
    # Calculate charges based on your logic
    charges = calculate_charges(user, book, issue_date, return_date)

    # Create a Bill instance
    bill = Bill(
        user=user,
        book=book,
        issuance_date=issue_date,
        due_date=return_date,
        charges=charges
    )
    bill.save()

    # Generate the bill PDF
    pdf_response = generate_bill_pdf(bill)

    return bill


def generate_bill_pdf(request, bill_id):
    # Retrieve the bill object
    bill = get_object_or_404(Bill, id=bill_id)

    # Get the username of the user who approved the book


    # Get the current date and time when the bill is generated
    bill_generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Define library watermark
    watermark = 'ALM'

    # Create a response for the PDF file
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="bill_{bill.id}.pdf"'

    # Create a PDF document using ReportLab
    doc = SimpleDocTemplate(response, pagesize=letter)
    story = []

    # Create a table for displaying bill data
    data = [
        ["Bill", ""],
        ["User:", str(bill.user.username)],

        ["Book:", str(bill.book.title)],
        ["Issuance Date:", str(bill.issuance_date)],
        ["Due Date:", str(bill.due_date)],
        ["Charges:", f"${bill.charges}"],
        ["Bill Generated At:", bill_generated_at],  # Date and time when the bill was generated
        ["Library:", watermark],  # Library watermark
    ]

    # Define table style
    style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)])

    # Create table
    bill_table = Table(data)
    bill_table.setStyle(style)

    # Add the table to the story
    story.append(bill_table)

    # Build the PDF document and return the response
    doc.build(story)

    return response

def bills_list(request):
    # Fetch a list of bills
    if request.user.is_superuser:
        # Superuser can see all user bills
        bills = Bill.objects.all()
    else:
        # Regular user can only see their own bills
        bills = Bill.objects.filter(user=request.user)
    # Render the bills_list.html template with the list of bills
    return render(request, 'bills_list.html', {'bills': bills})



# Create view for creating a new dealer
def create_dealer(request):
    if request.method == 'POST':
        form = Dealers2Form(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dealers/list.html')  # Redirect to a dealer list view
    else:
        form = Dealers2Form()
    return render(request, 'dealers/create.html', {'form': form})

# View for listing all dealers
def dealer_list(request):
    dealers = dealers2.objects.all()
    return render(request, 'dealers/list.html', {'dealers': dealers})

# View for updating a dealer
def update_dealer(request, dealer_id):
    dealer = get_object_or_404(dealers2, dealers_id=dealer_id)
    if request.method == 'POST':
        form = Dealers2Form(request.POST, instance=dealer)
        if form.is_valid():
            form.save()
            return redirect('list.html')
    else:
        form = Dealers2Form(instance=dealer)
    return render(request, 'dealers/update.html', {'form': form, 'dealer': dealer})

# View for deleting a dealer
def delete_dealer(request, dealer_id):
    dealer = get_object_or_404(dealers2, dealers_id=dealer_id)
    if request.method == 'POST':
        dealer.delete()
        return redirect('list.html')
    return render(request, 'dealers/delete.html', {'dealer': dealer})


# Create a new book
def create_book(request):
    dealers = dealers2.objects.all()
    print(dealers)
    if request.method == 'POST':
        form = Book2Form(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('/amsapp/book/list')
    else:
        form = Book2Form()
    return render(request, 'book/create_book.html', {'form': form,'dealers': dealers})

# List all books
def book_list(request):
    books = book2.objects.all()
    return render(request, 'book/book_list.html', {'books': books})

# Update an existing book
def update_book(request, book_id):
    book = get_object_or_404(book2, pk=book_id)
    if request.method == 'POST':
        form = Book2Form(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            return redirect('/amsapp/book/list')
    else:
        form = Book2Form(instance=book)
    return render(request, 'book/update_book.html', {'form': form})

# Delete an existing book
def delete_book(request, book_id):
    book = get_object_or_404(book2, pk=book_id)
    if request.method == 'POST':
        book.delete()
        return redirect('/amsapp/book/list')  # Updated line
    return render(request, 'book/delete_book.html', {'book': book})

# Create a new purchase
def create_purchase(request):
    books = book2.objects.all()
    dealers = dealers2.objects.all()
    if request.method == 'POST':
        form = Purchase2Form(request.POST)
        
        if form.is_valid():
            form.save()
            return redirect('purchase/purchase_list')
        else:
            print(form.errors)
    else:
        form = Purchase2Form()
    return render(request, 'purchase/create_purchase.html', {'form': form,'books':books,'dealers':dealers})

# List all purchases
def purchase_list(request):

    purchases = purchase2.objects.all()
    return render(request, 'purchase/purchase_list.html', {'purchases': purchases})

# Update an existing purchase
def update_purchase(request, purchase_id):
    purchase = get_object_or_404(purchase2, pk=purchase_id)
    if request.method == 'POST':
        form = Purchase2Form(request.POST, instance=purchase)
        if form.is_valid():
            form.save()
            return redirect('purchase/purchase_list')
    else:
        form = Purchase2Form(instance=purchase)
    return render(request, 'purchase/update_purchase.html', {'form': form})

# Delete an existing purchase
def delete_purchase(request, purchase_id):
    purchase = get_object_or_404(purchase2, pk=purchase_id)
    if request.method == 'POST':
        purchase.delete()
        return redirect('purchase/purchase_list')
    return render(request, 'purchase/delete_purchase.html', {'purchase': purchase})

# Create similar views for 'book2', 'purchase2', 'R_Purchase', 'BookStock2', and 'Book_transaction' models.

def book_stock(request):
    # Retrieve book stock records from the database
    stocks = BookStock2.objects.all()

    # Pass the data to the template
    return render(request, 'returnPurhase/bookstock.html', {'stocks': stocks})

def create_book_transaction(request):
    books = book2.objects.all()
    author = BookStock2.objects.all()
    if request.method == 'POST':
        form = BookTransactionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('book_transaction_list')
    else:
        form = BookTransactionForm()
    
    return render(request, 'book_transaction/book_transaction_form.html', {'form': form,'books':books,'author':author})

def book_transaction_list(request):
    
    transactions = Book_transaction.objects.all()
    return render(request, 'book_transaction/book_transaction_list.html', {'transactions': transactions})

@require_POST
def update_book_transaction(request, transaction_id):
    transaction = Book_transaction.objects.get(pk=transaction_id)
    form = BookTransactionForm(request.POST, instance=transaction)

    if form.is_valid():
        form.save()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'errors': form.errors})


@login_required
@ensure_csrf_cookie
def add_to_wishlist(request, book_id):
    if request.method == 'POST':
        form = WishlistItemForm(request.POST)
        if form.is_valid():
            # Check if the item is not already in the wishlist
            book_id = form.cleaned_data['book_id']
            book_isbn = form.cleaned_data['book_isbn']
            
            user = request.user

            if not WishlistItem.objects.filter(user=user, book_id=book_id).exists():
                WishlistItem.objects.create(user=user, book_id=book_id, book_isbn=book_isbn)
                return JsonResponse({'message': 'Item added to the wishlist.'})
            else:
                return JsonResponse({'error': 'Item already in the wishlist.'}, status=400)
        else:
            return JsonResponse({'error': 'Form data is invalid.', 'errors': form.errors}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)
    


def get_wishlist(request):
    user = request.user
    wishlist_items = WishlistItem.objects.filter(user=user)
    wishlist_data = []

    for item in wishlist_items:
        book_id = item.book_id
        book_isbn = item.book_isbn
        # Make an API request to Google Books to get book details by book_id
        google_books_url = f"https://www.googleapis.com/books/v1/volumes/{book_id}"
        params = {
            'q': f'isbn:{book_isbn}'
        }
        response = requests.get(google_books_url, params=params)
        if response.status_code == 200:
            book_data = response.json()
            wishlist_data.append({
                'item': item,
                'book_data': book_data,
            })
        else:
            wishlist_data.append('Data Not Found')

    return render(request, 'wishlist.html', {'wishlist_data': wishlist_data})


@login_required
def settings(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('settings')

    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }

    return render(request, 'settings.html', context)


def pushNtf(request):
   webpush_settings = getattr(settings, 'WEBPUSH_SETTINGS', {})
   vapid_key = webpush_settings.get('VAPID_PUBLIC_KEY')
   user = request.user
   return render(request, 'pushNtf.html', {user: user, 'vapid_key': vapid_key})

@require_POST
@csrf_exempt
def send_push(request):
    try:
        body = request.body
        data = json.loads(body)

        if 'head' not in data or 'body' not in data or 'id' not in data:
            return JsonResponse(status=400, data={"message": "Invalid data format"})

        user_id = data['id']
        user = get_object_or_404(User, pk=user_id)
        payload = {'head': data['head'], 'body': data['body']}
        send_user_notification(user=user, payload=payload, ttl=1000)

        return JsonResponse(status=200, data={"message": "Web push successful"})
    except TypeError:
        return JsonResponse(status=500, data={"message": "An error occurred"})
