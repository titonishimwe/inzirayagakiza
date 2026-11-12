from .contact_filters import get_contact_status_counts
from .models import ContentBlock, Question
from .permissions import user_is_pastor


def site_content(request):
    blocks = {}
    for block in ContentBlock.objects.filter(is_active=True):
        if block.block_type == ContentBlock.BlockType.IMAGE and block.image:
            blocks[block.key] = block.image.url
        else:
            blocks[block.key] = block.value

    pending_questions = 0
    pending_contacts = 0
    if request.user.is_authenticated:
        if user_is_pastor(request.user):
            pending_questions = Question.objects.filter(
                status=Question.Status.PENDING
            ).count()
            pending_contacts = get_contact_status_counts()['pending']
    return {
        'site_blocks': blocks,
        'dashboard_pending_questions': pending_questions,
        'dashboard_pending_contacts': pending_contacts,
    }
