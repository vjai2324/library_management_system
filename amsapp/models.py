from django.core.validators import MaxValueValidator
from django.db import models
from django.contrib.auth.models import User, AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models import Max
from django.forms import ValidationError
from django.utils import timezone


# Create your models here..

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile_number = models.CharField(max_length=15, help_text='Required. Enter your mobile number.')

    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)

    Address = models.CharField(max_length=100, help_text='Required. Enter address.')
    pincode = models.CharField(max_length=10, blank=True, null=True)
    district = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    postName = models.CharField(max_length=50, blank=True, null=True)
    

    def __str__(self):
        return f'{self.user.username} Profile'
 
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Associate carts with users
    items = models.ManyToManyField('Book')  # Assuming you have a Book model


class Book(models.Model):
    title = models.CharField(max_length=200)
    book_id = models.CharField(max_length=255, null=True)
    author = models.CharField(max_length=100)
    publication_date = models.CharField(max_length=10)
    description = models.TextField()
    cover_image = models.ImageField(upload_to='book_covers/', null=True, blank=True)
    category = models.CharField(max_length=255, null=True)
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    popularity = models.PositiveIntegerField(default=0)


    def str(self):
        return self.title


class GoogleBook(models.Model):
    book_id = models.CharField(max_length=255,null=True)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    published_date = models.CharField(max_length=10)  # You can adjust the field type
    description = models.TextField()

    def str(self):
        return self.title

class BookAvailabilityRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True, null=True)
    date_from = models.DateField(blank=True, null=True)
    date_to = models.DateField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    issuedbook = models.OneToOneField('IssuedBook', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Request for '{self.book}' by {self.user}"


class Request(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # User making the request
    message = models.TextField()  # The user's request message
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when the request was created

    def __str__(self):
        return f"Request by {self.user.username} ({self.created_at})"

class IssuedBook(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    issue_date = models.DateField()
    return_date = models.DateField()


class Bill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)  # Replace 'Book' with your book model
    issuance_date = models.DateField()
    due_date = models.DateField()
    charges = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Bill for {self.user} - {self.book}"


# jp code (stock mgmt)
# ok dealers2
class dealers2(models.Model):
    dealers_id = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=255, blank=False, unique=True)
    w_list = (("author", "author"), ("publisher", "publisher"), ("donator", "donator"))
    who = models.CharField('who', max_length=20, blank=False, choices=w_list, default="publisher")
    email = models.EmailField(max_length=254, unique=True, help_text="<em> abc@gmail.com <em>")
    s_list = (("live", "live"), ("block", "block"))
    status = models.CharField('status', max_length=20, choices=s_list, default="live")

    def str(self):
        return self.Name


class book2(models.Model):
    DoesNotExist = None
    book_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, help_text='bookName')  # title= bookname
    subtitle = models.CharField(max_length=255, help_text='Boo10k_Sub_Name')  # subtitle= book_sub_name
    author = models.CharField(max_length=255, null=True)
    category = models.CharField(max_length=255,
                                help_text='Religious , Epic, research paper, newspaper')  # category=Type of Book(Religious , Epic, research paper, newspaper, school and colleges study, compaction exams, etc )
    pub_date = models.DateField(help_text='Publication Date')
    description = models.TextField(help_text='Description')
    isbn_no = models.CharField(max_length=20, unique=True)
    pages = models.PositiveIntegerField(help_text="number of pages", blank=True, null=True)  # page count
    image = models.FileField(upload_to='uploads', blank=True, help_text='Book Cover Image')
    language = models.CharField(max_length=255, help_text="hindi")
    bookDealer = models.ForeignKey(dealers2, on_delete=models.CASCADE, default=None)  # oneToManyField

    def str(self):
        return f"{self.title} {self.author}"


class purchase2(models.Model):
    pid = models.AutoField(primary_key=True)
    book_title = models.ForeignKey(book2, on_delete=models.SET_NULL, to_field='book_id', related_name='purchases_as_title', null=True)
    dealers = models.ForeignKey(dealers2, on_delete=models.CASCADE)
    author = models.ForeignKey(book2, on_delete=models.CASCADE, related_name='purchases_as_author', null=True, blank=True)
    orderdate = models.DateField()
    bookquantity = models.PositiveIntegerField()
    perbookprice = models.PositiveIntegerField()
    totalprice = models.PositiveIntegerField(default=0, blank=True)
    get_book_pub_date = models.DateField()
    p_list = (
        ("cash", "cash"),
        ("net-banking", "net-banking"),
        ("UPI", "UPI"),
        ("Card", "Card"),
    )
    paymenttype = models.CharField('paymenttype', max_length=30, choices=p_list, default="cash")

    def str(self):
        return f"{self.book_title}"

    def save(self, *args, **kwargs):

        self.totalprice = self.bookquantity * self.perbookprice

        self.book_pub_date = self.book_title.pub_date

        try:
            stock = BookStock2.objects.get(book=self.book_title, author=self.author)
            stock.quantity_in_stock += self.bookquantity
            stock.save()
        except BookStock2.DoesNotExist:
            # If the Stock entry does not exist, create a new one
            stock = BookStock2(
                book=self.book_title,
                author=self.author,
                dealer=self.dealers,
                quantity_in_stock=self.bookquantity,
                purchase_price=self.perbookprice,  # You may adjust this as needed
                selling_price=self.perbookprice,  # You may adjust this as needed
                date_added=self.orderdate,  # Use orderdate as the date_added
            )
            stock.save()

        super().save(*args, **kwargs)


class R_Purchase(models.Model):
    rp_id = models.AutoField(primary_key=True)
    purchaseid = models.ForeignKey(purchase2, on_delete=models.CASCADE, default=None)
    bookquantity = models.PositiveIntegerField()
    perbookprice = models.PositiveIntegerField()
    Userid = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    def str(self):
        return f"{self.purchaseid}-{self.Userid}"


class BookStock2(models.Model):
    stock_id = models.AutoField(primary_key=True)
    book = models.ForeignKey(book2, on_delete=models.CASCADE, default=None,related_name='stocks')
    author = models.ForeignKey(book2, on_delete=models.CASCADE,  null=True, blank=True)
    dealer = models.ForeignKey(dealers2, on_delete=models.CASCADE, default=None)
    quantity_in_stock = models.IntegerField(default=0, help_text='Quantity available in stock')
    purchase_price = models.PositiveIntegerField(help_text='Price at which the book was purchased')
    selling_price = models.PositiveIntegerField(help_text='Price at which the book is sold')
    date_added = models.DateField(auto_now_add=True)

    def str(self):
        return f"{self.book} - {self.dealer} - Stock ID: {self.stock_id} --- {self.book}"

    def is_in_stock(self):
        return self.quantity_in_stock > 0

    def can_sell(self, requested_quantity):
        return self.quantity_in_stock >= requested_quantity

    def sell(self, requested_quantity):
        if self.can_sell(requested_quantity):
            # Update the quantity in stock when a book is sold
            self.quantity_in_stock -= requested_quantity
            self.save()
            return True
        else:
            return False
        
class Book_transaction(models.Model):
    tr_id = models.AutoField(primary_key=True)
    book = models.ForeignKey(BookStock2, on_delete=models.CASCADE, default=None)
    author = models.ForeignKey(book2, on_delete=models.CASCADE, null=True, blank=True)
    username = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    bookquantity = models.PositiveIntegerField()
    checkout = models.DateTimeField(null=True, blank=True, default=timezone.now)
    checkin_date = models.DateTimeField(null=True, blank=True)
    perdayprice = models.BigIntegerField(blank=True)
    total_days = models.PositiveIntegerField(blank=True, null=True)
    totalPrice = models.PositiveIntegerField(blank=True, null=True)
    grandtotalprice = models.BigIntegerField(blank=True, null=True)
    paymenttype = models.CharField(
        'paymenttype',
        max_length=30,
        choices=(
            ("cash", "cash"),
            ("net-banking", "net-banking"),
            ("UPI", "UPI"),
            ("Card", "Card"),
        ),
        default="cash"
    )
    def str(self):
        return f"{self.book} - {self.username.name}"

    def save(self, *args, **kwargs):
        if self.checkout and not self.checkin_date:
            try:
                book_stock = BookStock2.objects.get(stock_id=self.book.stock_id)
                if book_stock.quantity_in_stock >= self.bookquantity:
                    # Update the BookStock2 model when a book is checked out
                    book_stock.quantity_in_stock -= self.bookquantity
                    book_stock.save()
                else:
                    raise ValidationError("Insufficient stock for this book.")
            except BookStock2.DoesNotExist:
                raise ValidationError("Stock entry not found for this book and author.")
        elif self.checkin_date:
            try:
                book_stock = BookStock2.objects.get(stock_id=self.book.stock_id)
                book_stock.quantity_in_stock += self.bookquantity
                book_stock.save()
            except BookStock2.DoesNotExist:
                book_stock = BookStock2(
                    stock_id=self.book.stock_id,
                    quantity_in_stock=self.bookquantity,
                )
                book_stock.save()

        super().save(*args, **kwargs)
    

class WishlistItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book_id = models.CharField(max_length=255, default=None)  # Use CharField to accept both numbers and alphabets
    book_isbn = models.CharField(max_length=255, default=None)  # Use CharField to accept both numbers and alphabets
    added_at = models.DateTimeField(auto_now_add=True)

