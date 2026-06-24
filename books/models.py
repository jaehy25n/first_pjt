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

class LoanSignal(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='loan_signals')
    scope = models.CharField(max_length=50)
    value = models.FloatField()

    def __str__(self):
        return f"{self.book.title} - {self.scope}: {self.value}"

class CoLoan(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='coloans_as_base')
    co_book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='coloans_as_target')
    score = models.FloatField()

    class Meta:
        unique_together = ('book', 'co_book')

    def __str__(self):
        return f"{self.book.title} -> {self.co_book.title} ({self.score})"

class BookEmbedding(models.Model):
    """내용 기반 임베딩 벡터(오프라인 계산·저장). 런타임은 이 벡터로 코사인만 (D30)."""
    book = models.OneToOneField(Book, on_delete=models.CASCADE, related_name='embedding', primary_key=True)
    model = models.CharField(max_length=50)        # 예: text-embedding-3-small
    vector = models.JSONField()                     # float 리스트(1536d)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.book.title} emb({self.model})"
