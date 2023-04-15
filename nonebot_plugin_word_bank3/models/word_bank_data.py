from tortoise import fields
from tortoise.models import Model
from typing import List


class WordBankData(Model):
    id = fields.IntField(pk=True, generated=True)
    answer = fields.TextField()

    class Meta:
        table = "wordbank3_data"
        table_description = "wordbank3 答句数据库"

    @staticmethod
    async def ans_return(ans: str) -> List[int]:
        id_list = []
        wb_list = await WordBankData.filter(answer=ans).values()
        for wb in wb_list:
            id_list.append(wb["id"])
        return id_list

    @staticmethod
    async def id_return(id: int) -> List[str]:
        ans_list = []
        wb_list = await WordBankData.filter(id=id).values()
        for wb in wb_list:
            result = ""
            result += str(wb["id"])
            result += " . "
            result += wb["answer"]
            ans_list.append(result)
        return ans_list
