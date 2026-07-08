from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.models.enums import NotificationType, NotificationReferenceType

class CreateNotificationSchema(BaseModel):
    userId: str
    type: NotificationType
    title: str
    message: str
    referenceType: Optional[NotificationReferenceType] = None
    referenceId: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class NotificationQuerySchema(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=50)
    type: Optional[NotificationType] = None
    unreadOnly: bool = False
