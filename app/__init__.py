#===========================================================
# App Creation and Launch
#===========================================================

from flask import Flask, render_template, request, flash, redirect
import html
from PIL import Image
import io

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
# Team page route - Show details of a single team
#-----------------------------------------------------------
@app.get("/team/<string:code>")
def show_team_info(code):
    with connect_db() as client:
        # Get the thing details from the DB""
        sql = """SELECT code, name, description
            FROM teams 
            WHERE code=?"""
        params = [code]
        result = client.execute(sql, params)

        # Did we get a result?
        if result.rows:
            # yes, so show it on the page and get player info
            team = result.rows[0]
            sql = """SELECT name, notes, team
            FROM players
            WHERE team=?"""
            params = [code]
            players = client.execute(sql, params)

            return render_template("pages/team.jinja", team=team, players=players)

        else:
            # No, so show error
            return not_found_error()


#-----------------------------------------------------------
# Route for adding a player, using data posted from a form in the teams page
#-----------------------------------------------------------
@app.post("/add-player")
def add_player():
    # Get the data from the form
    name  = request.form.get("name")
    notes = request.form.get("notes")
    team = request.form.get("team")# Sanitise the text inputs
    
    name = html.escape(name)
    notes = html.escape(notes)
    team = html.escape(team)

    with connect_db() as client:
        # Add the team to the DB
        sql = "INSERT INTO players (name, notes, team) VALUES (?, ?, ?)"
        params = [name, notes, team]
        client.execute(sql, params)

        # Stay on teams page that we were on
        return redirect(f"/team/{team}")



#-----------------------------------------------------------
# Route for adding a team, using data posted from a form
#-----------------------------------------------------------
@app.post("/add-team")
def add_team():
    # Get the data from the form
    name  = request.form.get("name")
    code = request.form.get("code")
    desc = request.form.get("description")
    website = request.form.get("website")



    # Sanitise the text inputs
    name = html.escape(name)
    code = html.escape(code)
    desc = html.escape(desc)
    website = html.escape(website)



    # Get the uploaded image
    image_file = request.files['image']
    if not image_file:
        return server_error("Problem uploading image")

    # Reduce the image size for better performance
    MAX_SIZE = (500, 500)
    img = Image.open(image_file)
    img.thumbnail(MAX_SIZE)

    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    
    # Load the image data ready for the DB
    image_data = buffer.getvalue()    
    mime_type = image_file.mimetype

    with connect_db() as client:
        # Add the team to the DB
        sql = "INSERT INTO teams (code, name, description, website, image_data, image_mime) VALUES (?, ?, ?, ?, ?, ?)"
        params = [code, name, desc, website, image_data, mime_type]
        client.execute(sql, params)

        # Go back to the home page
        flash(f"Team '{name}' added", "success")
        return redirect("/")










#-----------------------------------------------------------
# Route for deleting a team, Id given in the route
#-----------------------------------------------------------
@app.get("/delete-team/<string:code>")
def delete_team(code):
    with connect_db() as client:
        # Delete the thing from the DB
        sql = "DELETE FROM teams WHERE code=?"
        params = [code]
        client.execute(sql, params)

        # Go back to the home page
        flash("Team deleted", "success")
        return redirect("/")


#-----------------------------------------------------------
# Route for serving an image from DB for a given team
#-----------------------------------------------------------
@app.route('/image/<string:code>')
def get_image(code):
    with connect_db() as client:
        sql = "SELECT image_data, image_mime FROM teams WHERE code = ?"
        params = [code]
        result = client.execute(sql, params)

        return image_file(result, "image_data", "image_mime")

