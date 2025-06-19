#===========================================================
# App Creation and Launch
#===========================================================

from flask import Flask, render_template, request, flash, redirect
import html

from app.helpers.session import init_session
from app.helpers.db      import connect_db
from app.helpers.errors  import init_error, server_error, not_found_error
from app.helpers.logging import init_logging
from app.helpers.images  import image_file
from app.helpers.time    import init_datetime, utc_timestamp, utc_timestamp_now


# Create the app
app = Flask(__name__)

# Configure app
init_session(app)   # Setup a session for messages, etc.
init_logging(app)   # Log requests
init_error(app)     # Handle errors and exceptions
init_datetime(app)  # Handle UTC dates in timestamps


#-----------------------------------------------------------
# Home page route
#-----------------------------------------------------------
@app.get("/")
def index():
    with connect_db() as client:
        # Get all the teams from the DB
        sql = "SELECT code, name, description FROM teams ORDER BY name ASC"
        params = []
        result = client.execute(sql, params)
        teams = result.rows

        # And show them on the page
        return render_template("pages/home.jinja", teams=teams)

        


#-----------------------------------------------------------
# Things page route - Show all the things, and new thing form
#-----------------------------------------------------------
@app.get("/things/")


#-----------------------------------------------------------
# Thing page route - Show details of a single thing
#-----------------------------------------------------------
@app.get("/team/<string:id>")
def show_team_info(id):
    with connect_db() as client:
        # Get the thing details from the DB
        sql = "SELECT code, name, description FROM teams WHERE code=?"
        params = [id]
        result = client.execute(sql, params)

        # Did we get a result?
        if result.rows:
            # yes, so show it on the page
            team = result.rows[0]
            return render_template("pages/team.jinja", team=team)

        else:
            # No, so show error
            return not_found_error()


#-----------------------------------------------------------
# Route for adding a thing, using data posted from a form
#-----------------------------------------------------------
@app.post("/add")
def add_a_thing():
    # Get the data from the form
    name  = request.form.get("name")
    price = request.form.get("price")

    # Sanitise the text inputs
    name = html.escape(name)

    # Get the uploaded image
    image_file = request.files['image']
    if not image_file:
        return server_error("Problem uploading image")

    # Load the image data ready for the DB
    image_data = image_file.read()
    mime_type = image_file.mimetype

    with connect_db() as client:
        # Add the thing to the DB
        sql = "INSERT INTO things (name, price, image_data, image_mime) VALUES (?, ?, ?, ?)"
        params = [name, price, image_data, mime_type]
        client.execute(sql, params)

        # Go back to the home page
        flash(f"Thing '{name}' added", "success")
        return redirect("/things")


#-----------------------------------------------------------
# Route for deleting a thing, Id given in the route
#-----------------------------------------------------------
@app.get("/delete/<int:id>")
def delete_a_thing(id):
    with connect_db() as client:
        # Delete the thing from the DB
        sql = "DELETE FROM things WHERE id=?"
        params = [id]
        client.execute(sql, params)

        # Go back to the home page
        flash("Thing deleted", "success")
        return redirect("/things")


#-----------------------------------------------------------
# Route for serving an image from DB for a given thing
#-----------------------------------------------------------
@app.route('/image/<int:id>')
def get_image(id):
    with connect_db() as client:
        sql = "SELECT image_data, image_mime FROM things WHERE id = ?"
        params = [id]
        result = client.execute(sql, params)

        return image_file(result, "image_data", "image_mime")

