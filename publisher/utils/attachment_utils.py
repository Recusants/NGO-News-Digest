# utils/attachment_utils.py
from django.contrib.contenttypes.models import ContentType
from publisher.models import GenericAttachment

def attach_file_to_object(obj, file):
    """
    Attach a single file to any Django model instance
    """
    
    content_type = ContentType.objects.get_for_model(obj.__class__)
    
    # Check if this is an update to existing file with same name
    existing_attachment = GenericAttachment.objects.filter(
        content_type=content_type,
        object_id=obj.id,
        file_name=file.name
    ).first()
    
    if existing_attachment:
        # Update existing file
        existing_attachment.file = file
        existing_attachment.save()
        return existing_attachment
    else:
        # Create new attachment
        attachment = GenericAttachment(
            content_object=obj,
            file=file
        )
        attachment.save()
        return attachment

def attach_multiple_files_to_object(obj, files):
    """
    Attach multiple files to any Django model instance
    Returns list of created attachments
    """
    attachments = []
    for file in files:
        attachment = attach_file_to_object(obj, file)
        attachments.append(attachment)
    return attachments

def get_attachments_for_object(obj):
    """
    Get all attachments for any Django model instance
    """
    
    content_type = ContentType.objects.get_for_model(obj.__class__)
    return GenericAttachment.objects.filter(
        content_type=content_type,
        object_id=obj.id
    ).order_by('order', 'uploaded_at')

def delete_attachment(attachment_id):
    """
    Delete a specific attachment
    """
    try:
        attachment = GenericAttachment.objects.get(id=attachment_id)
        attachment.delete()
        return True
    except GenericAttachment.DoesNotExist:
        return False