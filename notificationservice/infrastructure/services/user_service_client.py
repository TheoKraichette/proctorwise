import os
import httpx
from typing import List, Optional


class UserServiceClient:
    """Client to communicate with the UserService to get user information."""

    def __init__(self):
        self.base_url = os.getenv("USER_SERVICE_URL", "http://userservice:8000")

    async def get_users_by_role(self, role: str) -> List[dict]:
        """Get all active users with a specific role."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/users/role/{role}")
                if response.status_code == 200:
                    return response.json()
                return []
        except Exception as e:
            print(f"Error fetching users by role {role}: {e}")
            return []

    async def get_proctors(self) -> List[dict]:
        """Get all active proctors."""
        return await self.get_users_by_role("proctor")

    async def get_teachers(self) -> List[dict]:
        """Get all active teachers."""
        return await self.get_users_by_role("teacher")

    async def get_admins(self) -> List[dict]:
        """Get all active admins."""
        return await self.get_users_by_role("admin")

    async def get_user(self, user_id: str) -> Optional[dict]:
        """Get a specific user by ID."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/users/{user_id}")
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            print(f"Error fetching user {user_id}: {e}")
            return None


class ReservationServiceClient:
    """Client to communicate with the ReservationService to get exam information."""

    def __init__(self):
        self.base_url = os.getenv("RESERVATION_SERVICE_URL", "http://reservationservice:8000")

    async def get_exam(self, exam_id: str) -> Optional[dict]:
        """Get exam details including teacher_id."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/exams/{exam_id}")
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            print(f"Error fetching exam {exam_id}: {e}")
            return None
