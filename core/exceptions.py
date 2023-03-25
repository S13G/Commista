from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None and 'non_field_errors' in response.data:
        response.data['error'] = response.data.pop('non_field_errors')

    return response
