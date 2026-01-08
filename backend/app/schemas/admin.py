from pydantic import BaseModel

class StatsResponse(BaseModel):
    total_users: int
    total_groups: int
    total_students: int
    total_lectures: int
    active_labs: int
    total_submissions: int

class DeleteResponse(BaseModel):
    status: str

