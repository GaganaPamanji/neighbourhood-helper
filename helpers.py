def get_task_status_class(status):
    """Returns appropriate Bootstrap CSS class based on task status."""
    status_classes = {
        'open': 'primary',
        'assigned': 'warning',
        'completed': 'success',
        'cancelled': 'danger'
    }
    return status_classes.get(status, 'secondary')
