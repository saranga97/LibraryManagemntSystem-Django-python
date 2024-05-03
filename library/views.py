from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Book, BorrowRecord
from .forms import BookForm, BorrowForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegistrationForm, UserLoginForm
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import BorrowRecord
from django.http import HttpResponse
from django.http import JsonResponse
from django.contrib.auth import logout as django_logout
from django.contrib.auth.models import User
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .forms import UserRegistrationForm
from .models import BorrowRecord
from django.http import HttpResponseBadRequest
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages

def get_users(request):
    users = list(User.objects.all().values('username', 'email'))  # Fetch username and email fields
    return JsonResponse(users, safe=False)


class SignUpView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('user_login')  # Redirect to login page after successful sign up
    template_name = 'signup.html'  # Create a signup.html template for the sign-up form



def user_logout(request):
    # Call Django's logout function to logout the user
    django_logout(request)
    # Redirect to the user login page
    return redirect('user_login')  # Assuming 'user_login' is the name of your user login URL


@login_required
def my_books(request):
    borrowed_books = BorrowRecord.objects.filter(borrower=request.user)
    return render(request, 'my_books.html', {'borrowed_books': borrowed_books})





def user_register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')  # Get email from the form
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Check if passwords match
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('user_register')

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('user_register')

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('user_register')

        # Create the user
        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()

        messages.success(request, 'User created successfully.')
        return redirect('user_login')
    return render(request, 'user_register.html')


def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data.get('username')  # Get username or email from form
            password = form.cleaned_data.get('password')

            # Check if username_or_email is an email address
            if '@' in username_or_email:
                # If it's an email address, try to authenticate using email
                user = authenticate(email=username_or_email, password=password)
            else:
                # Otherwise, try to authenticate using username
                user = authenticate(username=username_or_email, password=password)

            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                form.add_error(None, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    return render(request, 'user_login.html', {'form': form})


def return_book(request, record_id):
    if request.method == 'POST':
        # Retrieve the borrow record by ID or return a 404 error if not found
        borrow_record = get_object_or_404(BorrowRecord, pk=record_id)

        # Check if the book has already been returned
        if borrow_record.returned:
            return HttpResponseBadRequest("The book has already been returned.")

        # Mark the book as returned
        borrow_record.returned = True
        borrow_record.save()

        # Set the book as available again
        book = borrow_record.book
        book.is_available = True
        book.save()

        # Redirect back to the borrowed books page
        return redirect('my_books')  # Assuming 'my_books' is the URL name for the borrowed books page
    else:
        return HttpResponseBadRequest("Invalid request method.")


def dashboard(request):
    user = request.user
    context = {
        'user': user,
    }
    return render(request, 'dashboard.html', context)


def admin_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and user.is_staff:
                login(request, user)
                return redirect('admin_dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'admin_login.html', {'form': form})


def admin_dashboard(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')  # Redirect to the admin dashboard after adding a book
    else:
        form = BookForm()

    admin_user = request.user

    # Retrieve all books from the database
    books = Book.objects.all()
    borrowrecords = BorrowRecord.objects.all()

    return render(request, 'admin_dashboard.html', {'admin_user': admin_user, 'form': form, 'books': books, 'borrowrecords' : borrowrecords})


def catalog(request):
    books = Book.objects.filter(is_available=True)
    return render(request, 'catalog.html', {'books': books})


def edit_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    if request.method == 'POST':
        # Process the form data and update the book
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        # Display the form to edit the book
        form = BookForm(instance=book)
    return render(request, 'edit_book.html', {'form': form, 'book': book})


def remove_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    book.delete()
    return redirect('admin_dashboard')


def borrow_book(request):
    if request.method == 'POST':
        form = BorrowForm(request.POST)
        if form.is_valid():
            book_id = form.cleaned_data['book_id']
            book = Book.objects.get(pk=book_id)
            if book.is_available:
                # Set the due date based on the current date and the borrowing period (e.g., 7 days)
                due_date = timezone.now() + timezone.timedelta(days=7)

                # Create a new BorrowRecord instance with the due_date set
                borrow_record = BorrowRecord(book=book, borrower=request.user, due_date=due_date)
                borrow_record.save()

                # Update the availability of the book
                book.is_available = False
                book.save()

                return redirect('catalog')
    else:
        form = BorrowForm()
    return render(request, 'borrow.html', {'form': form})


# def return_book(request, book_id):
#     book = Book.objects.get(pk=book_id)
#     borrow_record = BorrowRecord.objects.get(book=book, returned=False)
#     borrow_record.returned = True
#     borrow_record.save()
#     book.is_available = True
#     book.save()
#     return redirect('catalog')


def add_book(request):
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title')
        author = request.POST.get('author')
        isbn = request.POST.get('isbn')
        category = request.POST.get('category')

        # Create and save the new book
        new_book = Book(title=title, author=author, isbn=isbn, category=category)
        new_book.save()

        # Return a JSON response indicating success
        return JsonResponse({'success': True})
    else:
        # Return a JSON response indicating failure
        return JsonResponse({'success': False})
