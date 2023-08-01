import datetime

from bson import ObjectId
from discord.ext import commands
import discord
from utils.mongo import Document


class ShiftManagement:
    def __init__(self, connection, current_shifts):
        self.shifts = Document(connection, current_shifts)

    async def add_shift_by_user(
        self, member: discord.Member, shift_type: str, breaks: list, guild: int
    ):
        """
        Adds a shift for the specified user to the database, with the provided
        extras data.

        The shift is recorded as a document in the 'shifts' collection, and the
        user's ID is used as the document ID. If a document with that ID already
        exists in the collection, the new shift data is added to the existing
        'data' array.

        {
          "Username": "1FriendlyDoge",
          "Nickname": "NoobyNoob",
          "UserID": 123456789012345678,
          "Type": "Ingame Shift",
          "StartEpoch": 706969420,
          "Breaks": [
            {
              "StartEpoch": 706969430,
              "EndEpoch": 706969550
            }
          ],
          "Moderations": [
                ObjectId("123456789012345678901234")
          ],
          "EndEpoch": 706969420,
          "Guild": 12345678910111213
        }
        """
        data = {
            "_id": ObjectId(),
            "Username": member.name,
            "Nickname": member.display_name,
            "UserID": member.id,
            "Type": shift_type,
            "StartEpoch": datetime.datetime.now().timestamp(),
            "Breaks": breaks,
            "Guild": guild,
            "Moderations": [],
            "AddedTime": 0,
            "RemovedTime": 0,
            "EndEpoch": 0,
        }
        await self.shifts.db.insert_one(data)
        return data["_id"]

    async def add_time_to_shift(self, identifier: str, seconds: int):
        """
        Adds time to the specified user's shift.
        """
        document = await self.shifts.db.find_one({"_id": ObjectId(identifier)})
        document["AddedTime"] += int(seconds)
        await self.shifts.update_by_id(document)
        return document

    async def remove_time_from_shift(self, identifier: str, seconds: int):
        """
        Removes time from the specified user's shift.
        """
        document = await self.shifts.db.find_one({"_id": ObjectId(identifier)})
        document["RemovedTime"] += int(seconds)
        await self.shifts.update_by_id(document)
        return document

    async def end_shift(self, identifier: str, guild_id: int | None = None):
        """
        Ends the specified user's shift.
        """

        document = await self.shifts.db.find_one({"_id": ObjectId(identifier)})
        if not document:
            raise ValueError("Shift not found.")

        if document["Guild"] != (guild_id if guild_id else document["Guild"]):
            raise ValueError("Shift not found.")

        document["EndEpoch"] = datetime.datetime.now().timestamp()

        for breaks in document["Breaks"]:
            if breaks["EndEpoch"] == 0:
                breaks["EndEpoch"] = int(datetime.datetime.now().timestamp())

        await self.shifts.update_by_id(document)
        return document

    async def get_current_shift(self, member: discord.Member, guild_id: int):
        """
        Gets the current shift for the specified user.
        """
        return await self.shifts.db.find_one(
            {"UserID": member.id, "EndEpoch": 0, "Guild": guild_id}
        )
