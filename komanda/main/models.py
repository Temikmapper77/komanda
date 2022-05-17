from django.db import models

class Categories(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name

# Create your models here.
class Spendings(models.Model):
    date = models.DateField()
    amount = models.DecimalField(max_digits=9, decimal_places=2, default=00.00)
    category = models.ForeignKey(Categories, on_delete=models.CASCADE)

class Incomes(models.Model):
    date = models.DateField()
    value = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name