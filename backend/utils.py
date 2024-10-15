from .models import (ChatSession)

def get_chat_session(user_id_a, user_id_b):
    chat_sessions = ChatSession.objects.filter(
        participants__id=user_id_a
    ).filter(
        participants__id=user_id_b
    )
    
    if chat_sessions.exists():
        return chat_sessions.first()
    else:
        chat_session = ChatSession.objects.create()
        chat_session.participants.add(user_id_a, user_id_b)
        chat_session.save()
        return chat_session
    
def get_messages_for_session(chat_session):
    return chat_session.messages.all().order_by('timestamp')