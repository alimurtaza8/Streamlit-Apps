import streamlit as st
import pandas as pd
import sqlite3
import os
import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import uuid
from PIL import Image
import io
import base64
from io import BytesIO
import re

# Set page configuration
st.set_page_config(
    page_title="Personal Library Manager",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define constants
DB_FILE = "library.db"
IMAGE_FOLDER = "book_covers"

# Create directories if they don't exist
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# Custom CSS for better UI
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .header-container {
        display: flex;
        align-items: center;
        margin-bottom: 20px;
    }
    .header-text {
        margin-left: 15px;
    }
    .stButton button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        font-weight: 600;
    }
    .book-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        transition: transform 0.3s;
    }
    .book-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .metrics-card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        text-align: center;
    }
    .tag {
        display: inline-block;
        background-color: #e1e1e1;
        padding: 3px 10px;
        border-radius: 15px;
        margin: 2px;
        font-size: 0.8em;
    }
    .rating-star {
        color: gold;
        font-size: 1.2em;
    }
    .status-badge {
        padding: 5px 10px;
        border-radius: 12px;
        font-weight: bold;
        display: inline-block;
    }
    .upload-section {
        border: 2px dashed #aaa;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    }
    .filter-section {
        background-color: #f5f5f5;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    div[data-testid="stSidebar"] {
        background-color: #f5f7f9;
        padding-top: 2rem;
    }
    .highlight {
        background-color: #fff3cd;
        padding: 3px;
        border-radius: 3px;
    }
</style>
""", unsafe_allow_html=True)

# Database functions
def init_db():
    """Initialize the database with required tables if they don't exist."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Create books table
    c.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        isbn TEXT,
        publisher TEXT,
        publication_year INTEGER,
        genre TEXT,
        tags TEXT,
        rating INTEGER,
        status TEXT,
        description TEXT,
        cover_path TEXT,
        date_added TEXT,
        last_modified TEXT,
        notes TEXT,
        pages INTEGER,
        read_pages INTEGER,
        start_date TEXT,
        finish_date TEXT
    )
    ''')
    
    # Create reading_sessions table
    c.execute('''
    CREATE TABLE IF NOT EXISTS reading_sessions (
        id TEXT PRIMARY KEY,
        book_id TEXT,
        date TEXT,
        pages_read INTEGER,
        minutes_spent INTEGER,
        notes TEXT,
        FOREIGN KEY (book_id) REFERENCES books (id)
    )
    ''')
    
    conn.commit()
    conn.close()

def add_book(book_data):
    """Add a new book to the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Generate a unique ID if not provided
    if 'id' not in book_data or not book_data['id']:
        book_data['id'] = str(uuid.uuid4())
    
    # Set current date for date_added if not provided
    if 'date_added' not in book_data or not book_data['date_added']:
        book_data['date_added'] = datetime.datetime.now().strftime("%Y-%m-%d")
    
    book_data['last_modified'] = datetime.datetime.now().strftime("%Y-%m-%d")
    
    columns = ', '.join(book_data.keys())
    placeholders = ', '.join(['?' for _ in book_data])
    values = list(book_data.values())
    
    query = f"INSERT INTO books ({columns}) VALUES ({placeholders})"
    
    try:
        c.execute(query, values)
        conn.commit()
        success = True
        message = "Book added successfully!"
    except sqlite3.Error as e:
        success = False
        message = f"Error adding book: {e}"
    finally:
        conn.close()
    
    return success, message, book_data['id']

def update_book(book_id, book_data):
    """Update an existing book in the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    book_data['last_modified'] = datetime.datetime.now().strftime("%Y-%m-%d")
    
    set_clause = ', '.join([f"{key} = ?" for key in book_data.keys()])
    values = list(book_data.values())
    values.append(book_id)
    
    query = f"UPDATE books SET {set_clause} WHERE id = ?"
    
    try:
        c.execute(query, values)
        conn.commit()
        success = True
        message = "Book updated successfully!"
    except sqlite3.Error as e:
        success = False
        message = f"Error updating book: {e}"
    finally:
        conn.close()
    
    return success, message

def delete_book(book_id):
    """Delete a book from the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    try:
        # Get the cover path for deletion
        c.execute("SELECT cover_path FROM books WHERE id = ?", (book_id,))
        result = c.fetchone()
        cover_path = result[0] if result else None
        
        # Delete book record
        c.execute("DELETE FROM books WHERE id = ?", (book_id,))
        
        # Delete associated reading sessions
        c.execute("DELETE FROM reading_sessions WHERE book_id = ?", (book_id,))
        
        conn.commit()
        success = True
        message = "Book deleted successfully!"
        
        # Delete cover file if exists
        if cover_path and os.path.exists(cover_path):
            os.remove(cover_path)
            
    except sqlite3.Error as e:
        success = False
        message = f"Error deleting book: {e}"
    finally:
        conn.close()
    
    return success, message

def get_book(book_id):
    """Retrieve a specific book from the database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = dict(c.fetchone() or {})
    
    conn.close()
    return book

def get_all_books(filters=None, sort_by="title", ascending=True):
    """Retrieve all books with optional filtering and sorting."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = "SELECT * FROM books"
    params = []
    
    if filters:
        conditions = []
        for key, value in filters.items():
            if value:
                if key == "title" or key == "author" or key == "genre" or key == "tags":
                    conditions.append(f"{key} LIKE ?")
                    params.append(f"%{value}%")
                elif key == "status":
                    conditions.append(f"{key} = ?")
                    params.append(value)
                elif key == "rating":
                    conditions.append(f"{key} >= ?")
                    params.append(value)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
    
    query += f" ORDER BY {sort_by} {'ASC' if ascending else 'DESC'}"
    
    c.execute(query, params)
    books = [dict(row) for row in c.fetchall()]
    
    conn.close()
    return books

def add_reading_session(session_data):
    """Add a new reading session to the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Generate a unique ID if not provided
    if 'id' not in session_data or not session_data['id']:
        session_data['id'] = str(uuid.uuid4())
    
    # Set current date if not provided
    if 'date' not in session_data or not session_data['date']:
        session_data['date'] = datetime.datetime.now().strftime("%Y-%m-%d")
    
    columns = ', '.join(session_data.keys())
    placeholders = ', '.join(['?' for _ in session_data])
    values = list(session_data.values())
    
    query = f"INSERT INTO reading_sessions ({columns}) VALUES ({placeholders})"
    
    try:
        c.execute(query, values)
        
        # Update book's read_pages
        c.execute("""
            UPDATE books 
            SET read_pages = (
                SELECT COALESCE(SUM(pages_read), 0)
                FROM reading_sessions
                WHERE book_id = ?
            )
            WHERE id = ?
        """, (session_data['book_id'], session_data['book_id']))
        
        conn.commit()
        success = True
        message = "Reading session added successfully!"
    except sqlite3.Error as e:
        success = False
        message = f"Error adding reading session: {e}"
    finally:
        conn.close()
    
    return success, message

def get_reading_sessions(book_id=None):
    """Retrieve reading sessions, optionally filtered by book."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    if book_id:
        c.execute("""
            SELECT rs.*, b.title as book_title 
            FROM reading_sessions rs
            JOIN books b ON rs.book_id = b.id
            WHERE rs.book_id = ?
            ORDER BY rs.date DESC
        """, (book_id,))
    else:
        c.execute("""
            SELECT rs.*, b.title as book_title 
            FROM reading_sessions rs
            JOIN books b ON rs.book_id = b.id
            ORDER BY rs.date DESC
        """)
    
    sessions = [dict(row) for row in c.fetchall()]
    
    conn.close()
    return sessions

def get_library_statistics():
    """Get statistics about the library."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    stats = {}
    
    # Total books
    c.execute("SELECT COUNT(*) FROM books")
    stats["total_books"] = c.fetchone()[0]
    
    # Books by status
    c.execute("""
        SELECT status, COUNT(*) as count
        FROM books
        GROUP BY status
    """)
    status_counts = {row[0]: row[1] for row in c.fetchall() if row[0]}
    stats["status_counts"] = status_counts
    
    # Books by genre
    c.execute("""
        SELECT genre, COUNT(*) as count
        FROM books
        WHERE genre IS NOT NULL AND genre != ''
        GROUP BY genre
        ORDER BY count DESC
        LIMIT 10
    """)
    genre_counts = {row[0]: row[1] for row in c.fetchall() if row[0]}
    stats["genre_counts"] = genre_counts
    
    # Top authors
    c.execute("""
        SELECT author, COUNT(*) as count
        FROM books
        GROUP BY author
        ORDER BY count DESC
        LIMIT 5
    """)
    author_counts = {row[0]: row[1] for row in c.fetchall() if row[0]}
    stats["author_counts"] = author_counts
    
    # Reading progress
    c.execute("""
        SELECT 
            SUM(pages) as total_pages,
            SUM(read_pages) as total_read_pages
        FROM books
        WHERE pages > 0
    """)
    progress = c.fetchone()
    stats["total_pages"] = progress[0] or 0
    stats["total_read_pages"] = progress[1] or 0
    
    # Reading sessions
    c.execute("""
        SELECT 
            COUNT(*) as total_sessions,
            SUM(pages_read) as total_pages_read,
            SUM(minutes_spent) as total_minutes
        FROM reading_sessions
    """)
    sessions = c.fetchone()
    stats["total_sessions"] = sessions[0] or 0
    stats["session_pages"] = sessions[1] or 0
    stats["session_minutes"] = sessions[2] or 0
    
    conn.close()
    return stats

def reset_database():
    """Reset the database by removing all data."""
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    
    # Remove cover images
    for file in os.listdir(IMAGE_FOLDER):
        file_path = os.path.join(IMAGE_FOLDER, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
    
    # Re-initialize the database
    init_db()
    return True

def export_library():
    """Export the library data to CSV."""
    conn = sqlite3.connect(DB_FILE)
    
    # Export books
    books_df = pd.read_sql_query("SELECT * FROM books", conn)
    sessions_df = pd.read_sql_query("SELECT * FROM reading_sessions", conn)
    
    conn.close()
    
    # Create a BytesIO object for each dataframe
    books_buffer = BytesIO()
    sessions_buffer = BytesIO()
    
    # Write the dataframes to csv
    books_df.to_csv(books_buffer, index=False)
    sessions_df.to_csv(sessions_buffer, index=False)
    
    # Get the CSV data
    books_csv = books_buffer.getvalue()
    sessions_csv = sessions_buffer.getvalue()
    
    return books_csv, sessions_csv

def import_library(books_csv, sessions_csv):
    """Import library data from CSV files."""
    try:
        books_df = pd.read_csv(books_csv)
        sessions_df = pd.read_csv(sessions_csv)
        
        conn = sqlite3.connect(DB_FILE)
        
        # Import books
        books_df.to_sql('books', conn, if_exists='replace', index=False)
        
        # Import reading sessions
        sessions_df.to_sql('reading_sessions', conn, if_exists='replace', index=False)
        
        conn.close()
        return True, "Library imported successfully!"
    except Exception as e:
        return False, f"Error importing library: {e}"
    
def save_book_cover(book_id, image_data):
    """Save book cover image to disk and return the file path."""
    if not image_data:
        return None
    
    # Create directory if it doesn't exist
    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)
    
    # Generate a unique filename based on book_id
    filename = f"{book_id}.jpg"
    filepath = os.path.join(IMAGE_FOLDER, filename)
    
    # Save the image
    image = image_data
    image.save(filepath)
    
    return filepath

def get_tags_list():
    """Get a list of all unique tags in the library."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute("SELECT tags FROM books WHERE tags IS NOT NULL AND tags != ''")
    tag_strings = c.fetchall()
    conn.close()
    
    all_tags = []
    for tag_string in tag_strings:
        if tag_string[0]:
            tags = [tag.strip() for tag in tag_string[0].split(',')]
            all_tags.extend(tags)
    
    # Remove duplicates and sort
    unique_tags = sorted(list(set(all_tags)))
    return unique_tags

def get_genres_list():
    """Get a list of all unique genres in the library."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute("SELECT DISTINCT genre FROM books WHERE genre IS NOT NULL AND genre != '' ORDER BY genre")
    genres = [row[0] for row in c.fetchall()]
    
    conn.close()
    return genres

# UI Components
def display_header():
    """Display the application header."""
    st.markdown(
        """
        <div class="header-container">
            <div style="font-size: 42px;">📚</div>
            <div class="header-text">
                <h1>Personal Library Manager</h1>
                <p>Organize, track, and explore your book collection</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def display_book_form(book=None, is_update=False):
    """Display form for adding or updating a book."""
    # Default empty book data
    if book is None:
        book = {
            'id': '',
            'title': '',
            'author': '',
            'isbn': '',
            'publisher': '',
            'publication_year': None,
            'genre': '',
            'tags': '',
            'rating': 0,
            'status': 'Unread',
            'description': '',
            'cover_path': '',
            'notes': '',
            'pages': 0,
            'read_pages': 0,
            'start_date': '',
            'finish_date': ''
        }
    
    with st.form(key="book_form"):
        # Basic information
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Title*", value=book.get('title', ''))
            author = st.text_input("Author*", value=book.get('author', ''))
            isbn = st.text_input("ISBN", value=book.get('isbn', ''))
            publisher = st.text_input("Publisher", value=book.get('publisher', ''))
            publication_year = st.number_input(
                "Publication Year",
                min_value=0,
                max_value=datetime.datetime.now().year,
                value=book.get('publication_year') or 0
            )
        
        with col2:
            # Get list of existing genres for dropdown
            existing_genres = get_genres_list()
            genre_options = [""] + existing_genres
            
            # Allow selection from existing or input of new genre
            use_existing_genre = st.checkbox("Select from existing genres", value=book.get('genre', '') in existing_genres)
            
            if use_existing_genre:
                selected_genre = st.selectbox(
                    "Genre",
                    options=genre_options,
                    index=0 if book.get('genre', '') not in genre_options else genre_options.index(book.get('genre', ''))
                )
                genre = selected_genre
            else:
                genre = st.text_input("Genre (enter new)", value=book.get('genre', ''))
            
            # Tags with suggestions
            existing_tags = get_tags_list()
            tags_help = "Separate multiple tags with commas"
            if existing_tags:
                tags_help += f". Existing tags: {', '.join(existing_tags[:5])}" + ("..." if len(existing_tags) > 5 else "")
            
            tags = st.text_input("Tags", value=book.get('tags', ''), help=tags_help)
            
            rating = st.slider("Rating", 0, 5, value=book.get('rating', 0))
            
            status_options = ["Unread", "Reading", "Completed", "On Hold", "Abandoned", "Wishlist"]
            status = st.selectbox(
                "Status",
                options=status_options,
                index=status_options.index(book.get('status', 'Unread')) if book.get('status', '') in status_options else 0
            )
        
        # Book details
        st.subheader("Book Details")
        col3, col4 = st.columns(2)
        
        with col3:
            pages = st.number_input("Total Pages", min_value=0, value=book.get('pages', 0) or 0)
            read_pages = st.number_input("Pages Read", min_value=0, max_value=pages if pages > 0 else None, value=book.get('read_pages', 0) or 0)
            
            # Date fields
            start_date = st.date_input(
                "Start Date",
                value=datetime.datetime.strptime(book.get('start_date', ''), "%Y-%m-%d").date() if book.get('start_date', '') else None,
                help="When did you start reading this book?",
                key="start_date"
            )
            
            finish_date = st.date_input(
                "Finish Date",
                value=datetime.datetime.strptime(book.get('finish_date', ''), "%Y-%m-%d").date() if book.get('finish_date', '') else None,
                help="When did you finish reading this book?",
                key="finish_date"
            )
        
        with col4:
            description = st.text_area("Description", value=book.get('description', ''), height=150)
            notes = st.text_area("Personal Notes", value=book.get('notes', ''), height=150)
        
        # Cover image upload
        st.subheader("Book Cover")
        
        if book.get('cover_path', '') and os.path.exists(book.get('cover_path', '')):
            st.image(book.get('cover_path', ''), width=150)
            keep_cover = st.checkbox("Keep existing cover", value=True)
        else:
            keep_cover = False
        
        cover_file = st.file_uploader("Upload Cover Image", type=["jpg", "jpeg", "png"])
        
        # Submit button
        submit_label = "Update Book" if is_update else "Add Book"
        submit = st.form_submit_button(submit_label)
        
        if submit:
            # Validate required fields
            if not title or not author:
                st.error("Title and author are required fields.")
                return None
            
            # Process the form data
            book_data = {
                'title': title,
                'author': author,
                'isbn': isbn,
                'publisher': publisher,
                'publication_year': publication_year if publication_year > 0 else None,
                'genre': genre,
                'tags': tags,
                'rating': rating,
                'status': status,
                'description': description,
                'notes': notes,
                'pages': pages,
                'read_pages': read_pages,
                'start_date': start_date.strftime("%Y-%m-%d") if start_date else None,
                'finish_date': finish_date.strftime("%Y-%m-%d") if finish_date else None
            }
            
            # Handle cover image
            if cover_file is not None:
                try:
                    image = Image.open(cover_file)
                    if is_update:
                        book_data['id'] = book.get('id')
                    else:
                        book_data['id'] = str(uuid.uuid4())
                    
                    filepath = save_book_cover(book_data['id'], image)
                    book_data['cover_path'] = filepath
                except Exception as e:
                    st.error(f"Error processing image: {e}")
                    return None
            elif is_update and not keep_cover:
                book_data['cover_path'] = None
            elif is_update and keep_cover:
                # Keep existing cover path
                book_data['cover_path'] = book.get('cover_path', '')
            
            return book_data
    
    return None

def display_reading_session_form(book_id=None, books=None):
    """Display form for adding a reading session."""
    with st.form(key="reading_session_form"):
        st.subheader("Add Reading Session")
        
        if books is None:
            books = get_all_books()
        
        # Convert books to options
        book_options = {book['id']: f"{book['title']} by {book['author']}" for book in books}
        
        # Create select box
        selected_book_id = st.selectbox(
            "Book",
            options=list(book_options.keys()),
            format_func=lambda x: book_options[x],
            index=list(book_options.keys()).index(book_id) if book_id in book_options else 0
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("Date", value=datetime.datetime.now().date())
            pages_read = st.number_input("Pages Read", min_value=1, value=10)
        
        with col2:
            minutes_spent = st.number_input("Minutes Spent", min_value=1, value=30)
            notes = st.text_area("Notes", height=100)
        
        submit = st.form_submit_button("Add Session")
        
        if submit:
            session_data = {
                'book_id': selected_book_id,
                'date': date.strftime("%Y-%m-%d"),
                'pages_read': pages_read,
                'minutes_spent': minutes_spent,
                'notes': notes
            }
            
            return session_data
    
    return None

def display_book_card(book, on_edit=None, on_delete=None):
    """Display a book card with details and action buttons."""
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        if book.get('cover_path') and os.path.exists(book.get('cover_path')):
            st.image(book['cover_path'], width=150)
        else:
            st.markdown(
                """
                <div style="width:100px; height:150px; background-color:#f0f0f0; 
                display:flex; align-items:center; justify-content:center; border-radius:5px;">
                    <span style="font-size:40px; color:#aaa;">📖</span>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    with col2:
        # Status badge
        status_colors = {
            "Unread": "#6c757d",   # Gray
            "Reading": "#007bff",  # Blue
            "Completed": "#28a745", # Green
            "On Hold": "#ffc107",  # Yellow
            "Abandoned": "#dc3545", # Red
            "Wishlist": "#17a2b8"   # Cyan
        }
        status_color = status_colors.get(book.get('status', 'Unread'), '#6c757d')
        
        st.markdown(
            f"""
            <div>
                <span class="status-badge" style="background-color: {status_color}; color: white;">
                    {book.get('status', 'Unread')}
                </span>
                <h3 style="margin-top:5px;">{book.get('title', 'Unknown Title')}</h3>
                <h4>by {book.get('author', 'Unknown Author')}</h4>
                
                <div style="margin-top:10px;">
                    {"".join(['<span class="rating-star">★</span>' for _ in range(book.get('rating', 0))])}
                    {"".join(['<span style="color:#ddd;">★</span>' for _ in range(5 - book.get('rating', 0))])}
                </div>
                
                <p style="margin-top:10px;">
                    {f"<strong>Genre:</strong> {book.get('genre')}<br>" if book.get('genre') else ""}
                    {f"<strong>Published:</strong> {book.get('publication_year')}<br>" if book.get('publication_year') else ""}
                    {f"<strong>Pages:</strong> {book.get('pages')}<br>" if book.get('pages') else ""}
                </p>
                
                <div style="margin-top:5px;">
                    {" ".join([f'<span class="tag">{tag.strip()}</span>' for tag in book.get('tags', '').split(',') if tag.strip()])}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Description excerpt
        if book.get('description'):
            description = book.get('description')
            description_short = description[:200] + '...' if len(description) > 200 else description
            st.markdown(f"<p><em>{description_short}</em></p>", unsafe_allow_html=True)
        
        # Reading progress
        if book.get('pages', 0) > 0:
            progress = min(100, int((book.get('read_pages', 0) / book.get('pages', 1)) * 100))
            st.progress(progress / 100)
            st.caption(f"Reading Progress: {progress}% ({book.get('read_pages', 0)}/{book.get('pages', 0)} pages)")
    
    with col3:
        # Action buttons
        st.button("View", key=f"view_{book.get('id')}", on_click=lambda: on_edit(book.get('id')) if on_edit else None)
        st.button("Edit", key=f"edit_{book.get('id')}", on_click=lambda: on_edit(book.get('id')) if on_edit else None)
        st.button("Delete", key=f"delete_{book.get('id')}", type="primary", on_click=lambda: on_delete(book.get('id')) if on_delete else None)

def display_reading_session_list(sessions):
    """Display a list of reading sessions."""
    if not sessions:
        st.info("No reading sessions recorded yet.")
        return
    
    st.subheader(f"Reading Sessions ({len(sessions)})")
    
    for session in sessions:
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{session.get('date')}** - {session.get('book_title', 'Unknown Book')}")
                st.caption(f"Pages read: {session.get('pages_read')} | Time spent: {session.get('minutes_spent')} minutes")
                
                if session.get('notes'):
                    with st.expander("Session notes"):
                        st.write(session.get('notes'))
            
            with col2:
                reading_speed = round(session.get('pages_read', 0) / (session.get('minutes_spent', 1) / 60), 1)
                st.metric("Pages/Hour", f"{reading_speed}")

def create_chart(data, chart_type, title):
    """Create a chart based on the provided data and type."""
    plt.figure(figsize=(10, 6))
    plt.title(title)
    
    if chart_type == "bar":
        chart = sns.barplot(x=list(data.keys()), y=list(data.values()))
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
    elif chart_type == "pie":
        plt.pie(list(data.values()), labels=list(data.keys()), autopct='%1.1f%%', startangle=90)
        plt.axis('equal')
    
    # Convert plot to base64 string
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()
    
    return image_base64

def display_library_statistics(stats):
    """Display library statistics and charts."""
    st.subheader("Library Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(
            """
            <div class="metrics-card">
                <h1 style="color:#007bff;">📚</h1>
                <h3>Total Books</h3>
                <h2>{}</h2>
            </div>
            """.format(stats.get("total_books", 0)),
            unsafe_allow_html=True
        )
    
    with col2:
        completed = stats.get("status_counts", {}).get("Completed", 0)
        percent_completed = round((completed / stats.get("total_books", 1)) * 100) if stats.get("total_books", 0) > 0 else 0
        st.markdown(
            """
            <div class="metrics-card">
                <h1 style="color:#28a745;">✓</h1>
                <h3>Completed</h3>
                <h2>{} ({}%)</h2>
            </div>
            """.format(completed, percent_completed),
            unsafe_allow_html=True
        )
    
    with col3:
        reading = stats.get("status_counts", {}).get("Reading", 0)
        st.markdown(
            """
            <div class="metrics-card">
                <h1 style="color:#17a2b8;">📖</h1>
                <h3>Currently Reading</h3>
                <h2>{}</h2>
            </div>
            """.format(reading),
            unsafe_allow_html=True
        )
    
    with col4:
        # Reading progress percentage
        total_pages = stats.get("total_pages", 0)
        read_pages = stats.get("total_read_pages", 0)
        progress_percent = round((read_pages / total_pages) * 100) if total_pages > 0 else 0
        st.markdown(
            """
            <div class="metrics-card">
                <h1 style="color:#ffc107;">📊</h1>
                <h3>Reading Progress</h3>
                <h2>{}%</h2>
                <p>{}/{} pages</p>
            </div>
            """.format(progress_percent, read_pages, total_pages),
            unsafe_allow_html=True
        )
    
    # Charts
    st.subheader("Library Analysis")
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        if stats.get("status_counts"):
            status_chart = create_chart(stats["status_counts"], "pie", "Books by Status")
            st.markdown(
                f"""
                <div style="text-align:center;">
                    <h4>Books by Status</h4>
                    <img src="data:image/png;base64,{status_chart}" style="max-width:100%;">
                </div>
                """,
                unsafe_allow_html=True
            )
    
    with chart_col2:
        if stats.get("genre_counts"):
            genre_chart = create_chart(stats["genre_counts"], "bar", "Top Genres")
            st.markdown(
                f"""
                <div style="text-align:center;">
                    <h4>Top Genres</h4>
                    <img src="data:image/png;base64,{genre_chart}" style="max-width:100%;">
                </div>
                """,
                unsafe_allow_html=True
            )
    
    # Reading activity
    st.subheader("Reading Activity")
    
    # Display reading statistics
    activity_col1, activity_col2, activity_col3 = st.columns(3)
    
    with activity_col1:
        total_sessions = stats.get("total_sessions", 0)
        st.markdown(
            """
            <div class="metrics-card">
                <h3>Reading Sessions</h3>
                <h2>{}</h2>
            </div>
            """.format(total_sessions),
            unsafe_allow_html=True
        )
    
    with activity_col2:
        total_minutes = stats.get("session_minutes", 0)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        st.markdown(
            """
            <div class="metrics-card">
                <h3>Total Reading Time</h3>
                <h2>{} hr {} min</h2>
            </div>
            """.format(hours, minutes),
            unsafe_allow_html=True
        )
    
    with activity_col3:
        pages_per_hour = round((stats.get("session_pages", 0) / (stats.get("session_minutes", 1) / 60)), 1) if stats.get("session_minutes", 0) > 0 else 0
        st.markdown(
            """
            <div class="metrics-card">
                <h3>Average Reading Speed</h3>
                <h2>{} pages/hour</h2>
            </div>
            """.format(pages_per_hour),
            unsafe_allow_html=True
        )

def display_library_management():
    """Display library management tools."""
    st.subheader("Library Management")
    
    # Export library
    if st.button("Export Library Data"):
        books_csv, sessions_csv = export_library()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="Download Books Data",
                data=books_csv,
                file_name="library_books.csv",
                mime="text/csv"
            )
        
        with col2:
            st.download_button(
                label="Download Reading Sessions Data",
                data=sessions_csv,
                file_name="library_sessions.csv",
                mime="text/csv"
            )
    
    # Import library
    with st.expander("Import Library Data"):
        st.warning("Importing data will replace your current library. Make sure to export your data first if you want to keep it.")
        
        books_file = st.file_uploader("Upload Books CSV", type=["csv"])
        sessions_file = st.file_uploader("Upload Reading Sessions CSV", type=["csv"])
        
        if st.button("Import Data") and books_file and sessions_file:
            success, message = import_library(books_file, sessions_file)
            if success:
                st.success(message)
            else:
                st.error(message)
    
    # Reset library
    with st.expander("Reset Library"):
        st.warning("This will delete all books and reading sessions. This action cannot be undone.")
        
        if st.button("Reset Library", type="primary"):
            if reset_database():
                st.success("Library reset successfully!")

# Main application
def main():
    """Main application function."""
    # Initialize the database if it doesn't exist
    init_db()
    
    # Set session state for navigation
    if 'page' not in st.session_state:
        st.session_state.page = 'library'
    
    if 'book_id' not in st.session_state:
        st.session_state.book_id = None
    
    if 'show_add_form' not in st.session_state:
        st.session_state.show_add_form = False
    
    if 'show_edit_form' not in st.session_state:
        st.session_state.show_edit_form = False
    
    if 'show_add_session' not in st.session_state:
        st.session_state.show_add_session = False
    
    # Navigation functions
    def set_page(page):
        st.session_state.page = page
        # Reset other states when changing pages
        st.session_state.book_id = None
        st.session_state.show_add_form = False
        st.session_state.show_edit_form = False
        st.session_state.show_add_session = False
    
    def show_add_book():
        st.session_state.show_add_form = True
        st.session_state.show_edit_form = False
    
    def show_edit_book(book_id):
        st.session_state.book_id = book_id
        st.session_state.show_edit_form = True
        st.session_state.show_add_form = False
    
    def show_add_session(book_id=None):
        st.session_state.book_id = book_id
        st.session_state.show_add_session = True
    
    def delete_book_prompt(book_id):
        st.session_state.book_id = book_id
        st.session_state.confirm_delete = True
    
    # Display header
    display_header()
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### Navigation")
        
        if st.button("📚 My Library", use_container_width=True):
            set_page('library')
        
        if st.button("📊 Statistics", use_container_width=True):
            set_page('stats')
        
        if st.button("📖 Reading Sessions", use_container_width=True):
            set_page('sessions')
        
        if st.button("⚙️ Settings", use_container_width=True):
            set_page('settings')
        
        st.markdown("---")
        
        if st.button("➕ Add New Book", type="primary", use_container_width=True):
            show_add_book()
        
        if st.button("📝 Add Reading Session", type="primary", use_container_width=True):
            show_add_session()
    
    # Display different pages based on navigation
    if st.session_state.page == 'library':
        st.title("My Library")
        
        # Filter section
        with st.expander("Filter Books", expanded=False):
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            
            with filter_col1:
                filter_title = st.text_input("Title Contains")
                filter_author = st.text_input("Author Contains")
            
            with filter_col2:
                filter_genre = st.selectbox("Genre", [""] + get_genres_list())
                filter_tags = st.text_input("Tags Contains")
            
            with filter_col3:
                filter_status = st.selectbox("Status", ["", "Unread", "Reading", "Completed", "On Hold", "Abandoned", "Wishlist"])
                filter_rating = st.slider("Minimum Rating", 0, 5, 0)
            
            sort_col1, sort_col2 = st.columns(2)
            
            with sort_col1:
                sort_by = st.selectbox("Sort By", ["title", "author", "publication_year", "rating", "status", "date_added"])
            
            with sort_col2:
                sort_order = st.radio("Sort Order", ["Ascending", "Descending"], horizontal=True)
        
        # Apply filters
        filters = {
            "title": filter_title,
            "author": filter_author,
            "genre": filter_genre,
            "tags": filter_tags,
            "status": filter_status,
            "rating": filter_rating
        }
        
        # Remove empty filters
        filters = {k: v for k, v in filters.items() if v}
        
        # Get books with filters and sorting
        books = get_all_books(filters, sort_by, sort_order == "Ascending")
        
        # Display books
        if not books:
            st.info("No books found. Add some books to your library!")
        else:
            st.subheader(f"Found {len(books)} books")
            
            for book in books:
                with st.container():
                    display_book_card(book, on_edit=show_edit_book, on_delete=delete_book_prompt)
                    st.markdown("---")
        
        # Add Book Form
        if st.session_state.show_add_form:
            st.markdown("---")
            st.header("Add New Book")
            
            book_data = display_book_form()
            
            if book_data:
                success, message, book_id = add_book(book_data)
                if success:
                    st.success(message)
                    st.session_state.show_add_form = False
                    # Refresh the page to show the new book
                    st.experimental_rerun()
                else:
                    st.error(message)
        
        # Edit Book Form
        if st.session_state.show_edit_form and st.session_state.book_id:
            st.markdown("---")
            st.header("Edit Book")
            
            book = get_book(st.session_state.book_id)
            
            if book:
                book_data = display_book_form(book, is_update=True)
                
                if book_data:
                    success, message = update_book(st.session_state.book_id, book_data)
                    if success:
                        st.success(message)
                        st.session_state.show_edit_form = False
                        # Refresh the page to show the updated book
                        st.experimental_rerun()
                    else:
                        st.error(message)
            else:
                st.error("Book not found.")
        
        # Delete Book Confirmation
        if 'confirm_delete' in st.session_state and st.session_state.confirm_delete:
            st.warning("Are you sure you want to delete this book? This action cannot be undone.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Yes, Delete"):
                    success, message = delete_book(st.session_state.book_id)
                    if success:
                        st.success(message)
                        # st.session_state.confirm_delete = False
                        # # Refresh the page to show the updated library
                        # st.experimental_rerun()
                        st.session_state.confirm_delete = False
                        # Refresh the page to show the updated list
                        st.experimental_rerun()
                    else:
                        st.error(message)
            
            with col2:
                if st.button("No, Cancel"):
                    st.session_state.confirm_delete = False
                    st.experimental_rerun()
    
    elif st.session_state.page == 'stats':
        st.title("Library Statistics")
        
        # Get library statistics
        stats = get_library_statistics()
        
        # Display statistics
        display_library_statistics(stats)
    
    elif st.session_state.page == 'sessions':
        st.title("Reading Sessions")
        
        # Get all reading sessions
        sessions = get_all_reading_sessions()
        
        # Display reading sessions
        display_reading_sessions(sessions)
        
        # Add Reading Session Form
        if st.session_state.show_add_session:
            st.markdown("---")
            st.header("Add Reading Session")
            
            # Get books for dropdown
            books = get_all_books()
            book_options = {str(book['id']): f"{book['title']} by {book['author']}" for book in books}
            
            # Pre-select book if book_id is provided
            selected_book = str(st.session_state.book_id) if st.session_state.book_id else None
            
            # Session form
            with st.form("add_session_form"):
                book_id = st.selectbox("Book", options=list(book_options.keys()), 
                                      format_func=lambda x: book_options.get(x, "Unknown"),
                                      index=list(book_options.keys()).index(selected_book) if selected_book in book_options else 0)
                
                session_date = st.date_input("Date", value=datetime.now().date())
                pages_read = st.number_input("Pages Read", min_value=1, value=10)
                minutes_spent = st.number_input("Time Spent (minutes)", min_value=1, value=30)
                notes = st.text_area("Session Notes")
                
                submit_button = st.form_submit_button("Add Session")
                
                if submit_button:
                    session_data = {
                        "book_id": int(book_id),
                        "date": session_date.strftime("%Y-%m-%d"),
                        "pages_read": pages_read,
                        "minutes_spent": minutes_spent,
                        "notes": notes
                    }
                    
                    success, message = add_reading_session(session_data)
                    if success:
                        st.success(message)
                        st.session_state.show_add_session = False
                        # Refresh the page to show the new session
                        st.experimental_rerun()
                    else:
                        st.error(message)
    
    elif st.session_state.page == 'settings':
        st.title("Settings")
        
        # Library management tools
        display_library_management()
        
        # Custom settings
        st.subheader("Appearance")
        theme = st.selectbox("Theme", ["Light", "Dark", "System Default"])
        
        # Save settings
        if st.button("Save Settings"):
            st.success("Settings saved successfully!")

def export_library():
    """Export library data to CSV format."""
    books = get_all_books()
    sessions = get_all_reading_sessions()
    
    # Create CSV for books
    books_df = pd.DataFrame(books)
    books_csv = books_df.to_csv(index=False)
    
    # Create CSV for reading sessions
    sessions_df = pd.DataFrame(sessions)
    sessions_csv = sessions_df.to_csv(index=False)
    
    return books_csv, sessions_csv

def import_library(books_file, sessions_file):
    """Import library data from CSV files."""
    try:
        # Read CSV files
        books_df = pd.read_csv(books_file)
        sessions_df = pd.read_csv(sessions_file)
        
        # Validate data structure
        required_book_columns = ['title', 'author', 'status']
        required_session_columns = ['book_id', 'date', 'pages_read', 'minutes_spent']
        
        if not all(col in books_df.columns for col in required_book_columns):
            return False, "Books CSV is missing required columns"
        
        if not all(col in sessions_df.columns for col in required_session_columns):
            return False, "Sessions CSV is missing required columns"
        
        # Reset the database
        reset_database()
        
        # Import books
        for _, row in books_df.iterrows():
            book_data = row.to_dict()
            # Remove id column if present
            if 'id' in book_data:
                del book_data['id']
            
            add_book(book_data)
        
        # Import sessions
        for _, row in sessions_df.iterrows():
            session_data = row.to_dict()
            # Remove id column if present
            if 'id' in session_data:
                del session_data['id']
            
            add_reading_session(session_data)
        
        return True, "Library data imported successfully!"
    
    except Exception as e:
        return False, f"Error importing data: {str(e)}"

def reset_database():
    """Reset the database by removing all books and reading sessions."""
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    try:
        c.execute("DELETE FROM books")
        c.execute("DELETE FROM reading_sessions")
        conn.commit()
        return True
    except Exception as e:
        print(f"Error resetting database: {str(e)}")
        return False
    finally:
        conn.close()

def get_library_statistics():
    """Get statistics about the library."""
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    stats = {}
    
    try:
        # Total books
        c.execute("SELECT COUNT(*) as count FROM books")
        stats["total_books"] = c.fetchone()["count"]
        
        # Books by status
        c.execute("SELECT status, COUNT(*) as count FROM books GROUP BY status")
        status_counts = {row["status"]: row["count"] for row in c.fetchall()}
        stats["status_counts"] = status_counts
        
        # Books by genre
        c.execute("SELECT genre, COUNT(*) as count FROM books WHERE genre != '' GROUP BY genre ORDER BY count DESC LIMIT 10")
        genre_counts = {row["genre"]: row["count"] for row in c.fetchall()}
        stats["genre_counts"] = genre_counts
        
        # Total pages and read pages
        c.execute("SELECT SUM(pages) as total_pages FROM books")
        stats["total_pages"] = c.fetchone()["total_pages"] or 0
        
        c.execute("""
            SELECT SUM(rs.pages_read) as read_pages
            FROM reading_sessions rs
        """)
        stats["total_read_pages"] = c.fetchone()["read_pages"] or 0
        
        # Reading sessions stats
        c.execute("SELECT COUNT(*) as count FROM reading_sessions")
        stats["total_sessions"] = c.fetchone()["count"]
        
        c.execute("SELECT SUM(minutes_spent) as total_minutes FROM reading_sessions")
        stats["session_minutes"] = c.fetchone()["total_minutes"] or 0
        
        c.execute("SELECT SUM(pages_read) as total_pages FROM reading_sessions")
        stats["session_pages"] = c.fetchone()["total_pages"] or 0
        
        return stats
    
    except Exception as e:
        print(f"Error getting library statistics: {str(e)}")
        return {}
    
    finally:
        conn.close()

def get_genres_list():
    """Get a list of all genres in the library."""
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    try:
        c.execute("SELECT DISTINCT genre FROM books WHERE genre != '' ORDER BY genre")
        genres = [row[0] for row in c.fetchall()]
        return genres
    
    except Exception as e:
        print(f"Error getting genres list: {str(e)}")
        return []
    
    finally:
        conn.close()

def display_header():
    """Display the application header."""
    st.markdown(
        """
        <style>
        .header {
            display: flex;
            align-items: center;
            padding: 1rem 0;
            border-bottom: 1px solid #e0e0e0;
            margin-bottom: 1rem;
        }
        .logo {
            font-size: 1.5rem;
            font-weight: bold;
            margin-right: 1rem;
        }
        .metrics-card {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #f8f9fa;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            height: 100%;
        }
        .metrics-card h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        .metrics-card h2 {
            font-size: 1.75rem;
            margin-bottom: 0.5rem;
        }
        .metrics-card h3 {
            font-size: 1rem;
            font-weight: normal;
            margin-bottom: 0.5rem;
            color: #6c757d;
        }
        .metrics-card p {
            font-size: 0.8rem;
            color: #6c757d;
        }
        </style>
        <div class="header">
            <div class="logo">📚 BookTracker</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def display_book_card(book, on_edit=None, on_delete=None):
    """Display a book card."""
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Book cover or placeholder
        st.image("https://via.placeholder.com/150x200?text=Book+Cover", width=150)
    
    with col2:
        # Book title and author
        st.markdown(f"### {book['title']}")
        st.markdown(f"**Author:** {book['author']}")
        
        # Book details
        details_col1, details_col2 = st.columns(2)
        
        with details_col1:
            st.markdown(f"**Status:** {book['status']}")
            st.markdown(f"**Genre:** {book['genre'] if book['genre'] else 'Not specified'}")
            st.markdown(f"**Year:** {book['publication_year'] if book['publication_year'] else 'Not specified'}")
        
        with details_col2:
            st.markdown(f"**Rating:** {'⭐' * book['rating'] if book['rating'] else 'Not rated'}")
            st.markdown(f"**Pages:** {book['pages'] if book['pages'] else 'Not specified'}")
            if book['status'] == 'Reading':
                st.markdown(f"**Progress:** {book['current_page']}/{book['pages']} pages ({round((book['current_page'] / book['pages']) * 100) if book['pages'] else 0}%)")
        
        # Book description
        if book['description']:
            with st.expander("Description"):
                st.write(book['description'])
        
        # Book tags
        if book['tags']:
            st.markdown(f"**Tags:** {book['tags']}")
        
        # Action buttons
        action_col1, action_col2, action_col3, action_col4 = st.columns(4)
        
        with action_col1:
            if on_edit:
                if st.button("Edit", key=f"edit_{book['id']}"):
                    on_edit(book['id'])
        
        with action_col2:
            if on_delete:
                if st.button("Delete", key=f"delete_{book['id']}"):
                    on_delete(book['id'])
        
        with action_col3:
            if st.button("Add Session", key=f"session_{book['id']}"):
                st.session_state.book_id = book['id']
                st.session_state.show_add_session = True
        
        with action_col4:
            # View reading sessions for this book
            if st.button("View Sessions", key=f"view_sessions_{book['id']}"):
                st.session_state.show_book_sessions = book['id']

def display_book_form(book=None, is_update=False):
    """Display the book form and return the collected data."""
    with st.form("book_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Title", value=book['title'] if book else "")
            author = st.text_input("Author", value=book['author'] if book else "")
            publication_year = st.number_input("Publication Year", min_value=0, max_value=datetime.now().year, value=int(book['publication_year']) if book and book['publication_year'] else 2020)
        
        with col2:
            genres = get_genres_list()
            genre_options = [""] + genres
            
            if book and book['genre'] and book['genre'] not in genre_options:
                genre_options.append(book['genre'])
            
            genre = st.selectbox("Genre", options=genre_options, index=genre_options.index(book['genre']) if book and book['genre'] in genre_options else 0)
            
            status_options = ["Unread", "Reading", "Completed", "On Hold", "Abandoned", "Wishlist"]
            status = st.selectbox("Status", options=status_options, index=status_options.index(book['status']) if book else 0)
            
            rating = st.slider("Rating", min_value=0, max_value=5, value=int(book['rating']) if book and book['rating'] else 0)
        
        # Additional fields
        pages = st.number_input("Total Pages", min_value=0, value=int(book['pages']) if book and book['pages'] else 0)
        
        if status == "Reading":
            current_page = st.number_input("Current Page", min_value=0, max_value=pages if pages > 0 else None, value=int(book['current_page']) if book and book['current_page'] else 0)
        else:
            current_page = 0
        
        description = st.text_area("Description", value=book['description'] if book else "")
        tags = st.text_input("Tags (comma separated)", value=book['tags'] if book else "")
        
        # Get the current date for date_added if this is a new book
        date_added = datetime.now().strftime("%Y-%m-%d")
        
        # Submit button
        submit_text = "Update Book" if is_update else "Add Book"
        submit_button = st.form_submit_button(submit_text)
        
        if submit_button:
            # Collect form data
            book_data = {
                "title": title,
                "author": author,
                "publication_year": publication_year,
                "genre": genre,
                "status": status,
                "rating": rating,
                "pages": pages,
                "current_page": current_page,
                 "description": description,
                "tags": tags
            }
            
            # Add date_added for new books
            if not is_update:
                book_data["date_added"] = date_added
            
            return book_data
        
        return None

def init_db():
    """Initialize the database if it doesn't exist."""
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            publication_year INTEGER,
            genre TEXT,
            status TEXT NOT NULL,
            rating INTEGER,
            pages INTEGER,
            current_page INTEGER,
            description TEXT,
            tags TEXT,
            date_added TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS reading_sessions (
            id INTEGER PRIMARY KEY,
            book_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            pages_read INTEGER NOT NULL,
            minutes_spent INTEGER NOT NULL,
            notes TEXT,
            FOREIGN KEY (book_id) REFERENCES books (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_book(book_data):
    """Add a new book to the database."""
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    try:
        # Extract values from book_data
        title = book_data.get('title')
        author = book_data.get('author')
        publication_year = book_data.get('publication_year')
        genre = book_data.get('genre')
        status = book_data.get('status')
        rating = book_data.get('rating')
        pages = book_data.get('pages')
        current_page = book_data.get('current_page')
        description = book_data.get('description')
        tags = book_data.get('tags')
        date_added = book_data.get('date_added', datetime.now().strftime("%Y-%m-%d"))
        
        # Validate required fields
        if not title or not author or not status:
            return False, "Title, author, and status are required fields.", None
        
        # Insert the book
        c.execute('''
            INSERT INTO books (title, author, publication_year, genre, status, rating, pages, current_page, description, tags, date_added)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, author, publication_year, genre, status, rating, pages, current_page, description, tags, date_added))
        
        book_id = c.lastrowid
        conn.commit()
        
        return True, "Book added successfully!", book_id
    
    except Exception as e:
        print(f"Error adding book: {str(e)}")
        return False, f"Error adding book: {str(e)}", None
    
    finally:
        conn.close()

def update_book(book_id, book_data):
    """Update an existing book in the database."""
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    try:
        # Extract values from book_data
        title = book_data.get('title')
        author = book_data.get('author')
        publication_year = book_data.get('publication_year')
        genre = book_data.get('genre')
        status = book_data.get('status')
        rating = book_data.get('rating')
        pages = book_data.get('pages')
        current_page = book_data.get('current_page')
        description = book_data.get('description')
        tags = book_data.get('tags')
        
        # Validate required fields
        if not title or not author or not status:
            return False, "Title, author, and status are required fields."
        
        # Update the book
        c.execute('''
            UPDATE books
            SET title = ?, author = ?, publication_year = ?, genre = ?, status = ?, 
                rating = ?, pages = ?, current_page = ?, description = ?, tags = ?
            WHERE id = ?
        ''', (title, author, publication_year, genre, status, rating, pages, current_page, description, tags, book_id))
        
        conn.commit()
        
        return True, "Book updated successfully!"
    
    except Exception as e:
        print(f"Error updating book: {str(e)}")
        return False, f"Error updating book: {str(e)}"
    
    finally:
        conn.close()

def delete_book(book_id):
    """Delete a book from the database."""
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    try:
        # Delete associated reading sessions first
        c.execute("DELETE FROM reading_sessions WHERE book_id = ?", (book_id,))
        
        # Delete the book
        c.execute("DELETE FROM books WHERE id = ?", (book_id,))
        
        conn.commit()
        
        return True, "Book deleted successfully!"
    
    except Exception as e:
        print(f"Error deleting book: {str(e)}")
        return False, f"Error deleting book: {str(e)}"
    
    finally:
        conn.close()

def get_book(book_id):
    """Get a book by its ID."""
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        c.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        book = c.fetchone()
        
        if book:
            return dict(book)
        else:
            return None
    
    except Exception as e:
        print(f"Error getting book: {str(e)}")
        return None
    
    finally:
        conn.close()

def get_all_books(filters=None, sort_by="title", ascending=True):
    """Get all books with optional filtering and sorting."""
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        query = "SELECT * FROM books"
        params = []
        
        # Apply filters if provided
        if filters:
            filter_conditions = []
            
            if "title" in filters:
                filter_conditions.append("title LIKE ?")
                params.append(f"%{filters['title']}%")
            
            if "author" in filters:
                filter_conditions.append("author LIKE ?")
                params.append(f"%{filters['author']}%")
            
            if "genre" in filters:
                filter_conditions.append("genre = ?")
                params.append(filters['genre'])
            
            if "tags" in filters:
                filter_conditions.append("tags LIKE ?")
                params.append(f"%{filters['tags']}%")
            
            if "status" in filters:
                filter_conditions.append("status = ?")
                params.append(filters['status'])
            
            if "rating" in filters and filters['rating'] > 0:
                filter_conditions.append("rating >= ?")
                params.append(filters['rating'])
            
            if filter_conditions:
                query += " WHERE " + " AND ".join(filter_conditions)
        
        # Apply sorting
        order_dir = "ASC" if ascending else "DESC"
        query += f" ORDER BY {sort_by} {order_dir}"
        
        c.execute(query, params)
        books = c.fetchall()
        
        return [dict(book) for book in books]
    
    except Exception as e:
        print(f"Error getting books: {str(e)}")
        return []
    
    finally:
        conn.close()

def add_reading_session(session_data):
    """Add a new reading session to the database."""
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    try:
        # Extract values from session_data
        book_id = session_data.get('book_id')
        date = session_data.get('date')
        pages_read = session_data.get('pages_read')
        minutes_spent = session_data.get('minutes_spent')
        notes = session_data.get('notes')
        
        # Validate required fields
        if not book_id or not date or not pages_read or not minutes_spent:
            return False, "Book, date, pages read, and time spent are required fields."
        
        # Insert the session
        c.execute('''
            INSERT INTO reading_sessions (book_id, date, pages_read, minutes_spent, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (book_id, date, pages_read, minutes_spent, notes))
        
        # Update book's current page if it's in "Reading" status
        c.execute("SELECT status, current_page, pages FROM books WHERE id = ?", (book_id,))
        book = c.fetchone()
        
        if book and book[0] == "Reading":
            current_page = book[1] or 0
            total_pages = book[2] or 0
            
            new_current_page = current_page + pages_read
            
            # Don't exceed total pages
            if total_pages > 0 and new_current_page > total_pages:
                new_current_page = total_pages
            
            c.execute("UPDATE books SET current_page = ? WHERE id = ?", (new_current_page, book_id))
            
            # If reached the end of the book, ask if want to mark as completed
            if total_pages > 0 and new_current_page >= total_pages:
                pass  # This will be handled in the UI
        
        conn.commit()
        
        return True, "Reading session added successfully!"
    
    except Exception as e:
        print(f"Error adding reading session: {str(e)}")
        return False, f"Error adding reading session: {str(e)}"
    
    finally:
        conn.close()

def get_all_reading_sessions(book_id=None):
    """Get all reading sessions, optionally filtered by book ID."""
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        if book_id:
            c.execute('''
                SELECT rs.*, b.title as book_title
                FROM reading_sessions rs
                JOIN books b ON rs.book_id = b.id
                WHERE rs.book_id = ?
                ORDER BY rs.date DESC
            ''', (book_id,))
        else:
            c.execute('''
                SELECT rs.*, b.title as book_title
                FROM reading_sessions rs
                JOIN books b ON rs.book_id = b.id
                ORDER BY rs.date DESC
            ''')
        
        sessions = c.fetchall()
        
        return [dict(session) for session in sessions]
    
    except Exception as e:
        print(f"Error getting reading sessions: {str(e)}")
        return []
    
    finally:
        conn.close()

def display_reading_sessions(sessions):
    """Display reading sessions."""
    if not sessions:
        st.info("No reading sessions found. Add some reading sessions to track your progress!")
        return
    
    st.subheader(f"Reading Sessions ({len(sessions)})")
    
    for session in sessions:
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{session.get('date')}** - {session.get('book_title', 'Unknown Book')}")
                st.caption(f"Pages read: {session.get('pages_read')} | Time spent: {session.get('minutes_spent')} minutes")
                
                if session.get('notes'):
                    with st.expander("Session notes"):
                        st.write(session.get('notes'))
            
            with col2:
                reading_speed = round(session.get('pages_read', 0) / (session.get('minutes_spent', 1) / 60), 1)
                st.metric("Pages/Hour", f"{reading_speed}")

if __name__ == "__main__":
    main()

                        
