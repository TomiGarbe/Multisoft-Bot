import uuid

class WebProvider:

    def send_text(self, channel_id: str, to: str, content: str):
        return {
            "provider_message_id": str(uuid.uuid4()),
            "status": "sent",
        }

    def send_media(self, channel_id: str, to: str, media_url: str, caption: str | None):
        return {
            "provider_message_id": str(uuid.uuid4()),
            "status": "sent",
        }

    def reply_to_message(self, channel_id: str, to: str, content: str, reply_to_id: str):
        return {
            "provider_message_id": str(uuid.uuid4()),
            "status": "sent",
        }