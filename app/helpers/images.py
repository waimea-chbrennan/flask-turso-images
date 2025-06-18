#===========================================================
# Image Related Functions
#===========================================================

from flask import send_file, make_response
from io import BytesIO
from app.helpers.errors import not_found_error


#-----------------------------------------------------------
# Return an image file from a DB query result
# - result - Database query result
# - data_column - Database BLOB column with image data
# - mime_column - Database TEXT column with mime type
#-----------------------------------------------------------
def image_file(result, data_column, mime_column):
    # Was there a result from the DB?
    if result.rows:
        # Yes, so create a file from the data
        response = make_response(send_file(
            BytesIO(result.rows[0][data_column]),
            mimetype=result.rows[0][mime_column]
        ))

        # Set cache headers (e.g. cache for 1 hour)
        response.headers["Cache-Control"] = "public, max-age=3600"

        # Return the file
        return response

    # No, so 404
    return not_found_error()

