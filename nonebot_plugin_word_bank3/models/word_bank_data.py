from tortoise import fields
from tortoise.models import Model


class WordBankData(Model):
    id = fields.IntField(pk=True, generated=True)
    answer = fields.TextField()

    class Meta:
        table = "wordbank3_data"
        table_description = "wordbank3 答句数据库"
