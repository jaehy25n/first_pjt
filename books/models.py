from django.db import models

class Library(models.Model):
    lib_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    region = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Book(models.Model):
    isbn13 = models.CharField(max_length=13, primary_key=True)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True)
    publisher = models.CharField(max_length=255, blank=True)
    pub_year = models.IntegerField(null=True, blank=True)
    kdc_code = models.CharField(max_length=20, blank=True)
    cover_url = models.URLField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    page_count = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.title

class Holding(models.Model):
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='holdings')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='holdings')
    has_book = models.BooleanField(default=False)
    loan_available = models.BooleanField(default=False)
    snapshot_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('library', 'book')

    def __str__(self):
        return f"{self.library.name} - {self.book.title} ({'대출가능' if self.loan_available else '대출불가'})"
