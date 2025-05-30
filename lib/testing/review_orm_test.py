from employee import Employee, CONN, CURSOR
from department import Department
from review import Review
import pytest


class TestReview:
    '''Class Review in review.py'''

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Drop all tables before each test for a clean slate."""
        CURSOR.execute("DROP TABLE IF EXISTS reviews")
        CURSOR.execute("DROP TABLE IF EXISTS employees")
        CURSOR.execute("DROP TABLE IF EXISTS departments")
        CONN.commit()
        yield
        # Optional: drop tables after test as well
        CURSOR.execute("DROP TABLE IF EXISTS reviews")
        CURSOR.execute("DROP TABLE IF EXISTS employees")
        CURSOR.execute("DROP TABLE IF EXISTS departments")
        CONN.commit()

    def create_all_tables(self):
        """Helper to create all tables in correct order for FK constraints."""
        Department.create_table()
        Employee.create_table()
        Review.create_table()

    def test_creates_table(self):
        """Contains method 'create_table()' that creates table 'reviews' if not exists."""
        self.create_all_tables()
        # Check reviews table exists
        CURSOR.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reviews'")
        assert CURSOR.fetchone() is not None

    def test_drops_table(self):
        """Contains method 'drop_table()' that drops 'reviews' table if exists."""

        self.create_all_tables()
        # Drop reviews table
        Review.drop_table()

        # Confirm employees table still exists
        CURSOR.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employees'")
        assert CURSOR.fetchone() is not None

        # Confirm reviews table does NOT exist
        CURSOR.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reviews'")
        assert CURSOR.fetchone() is None

    def test_saves_review(self):
        """Contains method 'save()' that saves Review instance and sets its id."""

        self.create_all_tables()
        department = Department("Payroll", "Building A, 5th Floor")
        department.save()

        employee = Employee("Sasha", "Manager", department.id)
        employee.save()

        review = Review(2023, "Excellent Python skills!", employee.id)
        review.save()

        CURSOR.execute("SELECT * FROM reviews")
        row = CURSOR.fetchone()

        assert (row[0], row[1], row[2], row[3]) == (review.id, review.year, review.summary, review.employee_id)

    def test_creates_review(self):
        """Contains method 'create()' that creates new db row and returns Review instance."""

        self.create_all_tables()
        department = Department("Payroll", "Building A, 5th Floor")
        department.save()

        employee = Employee.create("Kai", "Web Developer", department.id)

        review = Review.create(2023, "Excellent Python skills!", employee.id)

        CURSOR.execute("SELECT * FROM reviews")
        row = CURSOR.fetchone()

        assert (row[0], row[1], row[2], row[3]) == (review.id, review.year, review.summary, review.employee_id)

    def test_instance_from_db(self):
        """Contains method 'instance_from_db()' that takes db row and returns Review instance."""

        self.create_all_tables()
        department = Department.create("Payroll", "Building A, 5th Floor")
        employee = Employee.create("Raha", "Accountant", department.id)

        CURSOR.execute(
            "INSERT INTO reviews (year, summary, employee_id) VALUES (?, ?, ?)",
            (2022, 'Amazing coder!', employee.id)
        )
        CONN.commit()

        CURSOR.execute("SELECT * FROM reviews")
        row = CURSOR.fetchone()

        review = Review.instance_from_db(row)
        assert (row[0], row[1], row[2], row[3]) == (review.id, review.year, review.summary, review.employee_id)

    def test_finds_by_id(self):
        """Contains method 'find_by_id()' that returns Review instance by id."""

        self.create_all_tables()
        department = Department.create("Payroll", "Building A, 5th Floor")
        employee = Employee.create("Raha", "Accountant", department.id)

        review1 = Review.create(2020, "Great coder!", employee.id)
        id1 = review1.id
        review2 = Review.create(2000, "Awesome coder!", employee.id)
        id2 = review2.id

        review = Review.find_by_id(id1)
        assert (review.id, review.year, review.summary, review.employee_id) == (id1, 2020, "Great coder!", employee.id)

        review = Review.find_by_id(id2)
        assert (review.id, review.year, review.summary, review.employee_id) == (id2, 2000, "Awesome coder!", employee.id)

        # Should be None since no Review with id=99999 exists
        review = Review.find_by_id(99999)
        assert review is None

    def test_updates_row(self):
        """Contains method 'update()' that updates instance's db record."""

        self.create_all_tables()
        department = Department.create("Payroll", "Building A, 5th Floor")
        employee = Employee.create("Raha", "Accountant", department.id)

        review1 = Review.create(2020, "Usually double checks their work", employee.id)
        id1 = review1.id
        review2 = Review.create(2000, "Takes long lunches", employee.id)
        id2 = review2.id

        review1.year = 2023
        review1.summary = "Always double checks their work"
        review1.update()

        # Confirm review1 updated
        review = Review.find_by_id(id1)
        assert (review.id, review.year, review.summary, review.employee_id) == (id1, 2023, "Always double checks their work", employee.id)

        # Confirm review2 not updated
        review = Review.find_by_id(id2)
        assert (review.id, review.year, review.summary, review.employee_id) == (id2, 2000, "Takes long lunches", employee.id)

    def test_deletes_row(self):
        """Contains method 'delete()' that deletes instance's corresponding db record."""

        self.create_all_tables()
        department = Department.create("Payroll", "Building A, 5th Floor")
        employee = Employee.create("Raha", "Accountant", department.id)

        review1 = Review.create(2020, "Usually double checks their work", employee.id)
        id1 = review1.id
        review2 = Review.create(2000, "Takes long lunches", employee.id)
        id2 = review2.id

        review1.delete()

        # Assert row deleted
        assert Review.find_by_id(id1) is None
        # Assert Review object id cleared
        assert review1.id is None
        # Assert internal dict cache cleared if applicable
        if hasattr(Review, 'all'):
            assert Review.all.get(id1) is None

        # Confirm review2 row and object unchanged
        review = Review.find_by_id(id2)
        assert (review.id, review.year, review.summary, review.employee_id) == (id2, 2000, "Takes long lunches", employee.id)

    def test_gets_all(self):
        """Contains method 'get_all()' that returns list of Review instances for every record."""

        self.create_all_tables()
        department = Department.create("Payroll", "Building A, 5th Floor")
        employee = Employee.create("Raha", "Accountant", department.id)

        review1 = Review.create(2020, "Great coder!", employee.id)
        review2 = Review.create(2000, "Awesome coders!", employee.id)

        reviews = Review.get_all()
        assert len(reviews) == 2
        # Reviews may not be ordered - sort by id to check reliably
        reviews_sorted = sorted(reviews, key=lambda r: r.id)
        assert (reviews_sorted[0].id, reviews_sorted[0].year, reviews_sorted[0].summary, reviews_sorted[0].employee_id) == (review1.id, review1.year, review1.summary, review1.employee_id)
        assert (reviews_sorted[1].id, reviews_sorted[1].year, reviews_sorted[1].summary, reviews_sorted[1].employee_id) == (review2.id, review2.year, review2.summary, review2.employee_id)
