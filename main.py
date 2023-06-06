import psycopg2
from time import sleep
from email_validator import validate_email, EmailNotValidError


class Connector:
    '''
    This class creates connector to local postgresql db
    Allows to use methods to make CRUD operations with data
    '''

    def __init__(self, db, usr, password):
        self.db = db
        self.user = usr
        self.password = password
        self.conn = None

    def connect(self):
        if not self.conn:
            self.conn = psycopg2.connect(database=self.db, user=self.user, password=self.password)
        else:
            print('Connection already exist!')

    def close_connection(self):
        self.conn.close()

    def create_tables(self):
        with self.conn.cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS client(
                    client_id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    surname VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL
                );
                CREATE TABLE IF NOT EXISTS phones(
                    id SERIAL PRIMARY KEY,
                    client_id INTEGER REFERENCES client(client_id) ON DELETE CASCADE NOT NULL,
                    number VARCHAR(100) UNIQUE NOT NULL
                );
            ''')
            self.conn.commit()

    def add_client(self, name, surname, email):
        with self.conn.cursor() as cursor:
            request = '''
                INSERT INTO client(name, surname, email)
                VALUES(%s, %s, %s) RETURNING client_id
                '''
            try:
                cursor.execute(request, (name, surname, email))
                self.conn.commit()
                print(f'Client {surname} {name} with email {email} was created! ')
                sleep(1)
            except(Exception, psycopg2.Error) as error:
                self.conn.rollback()
                print(f"Error creating client: {error}")
                sleep(1)

    def update_client(self, client, to_change, new_value):
        with self.conn.cursor() as cursor:
            request = '''
                      UPDATE client
                      SET {} = %s
                      WHERE client_id = %s
                      '''.format(to_change)
            try:
                cursor.execute(request, (new_value, client[0]))
                self.conn.commit()
                print(f'Client {client[1]} {client[2]} was updated.')
                sleep(1)
            except(Exception, psycopg2.Error) as error:
                print(f"Error updating client: {error}")
                sleep(1)

    def add_phone_number(self, client_id, phone):
        with self.conn.cursor() as cursor:
            request = '''
                       INSERT INTO phones(client_id, number)
                       VALUES(%s, %s)
                       '''
            try:
                cursor.execute(request, (client_id, phone))
                self.conn.commit()
                print(f'Phone number: {phone} was successfully added!')
                sleep(1)
            except(Exception, psycopg2.Error) as error:
                print(f"Error adding phone number: {error}")
                sleep(1)

    def delete_number(self, phone_number):
        with self.conn.cursor() as cursor:
            request = '''
                       DELETE FROM phones
                       WHERE number = %s
                      '''
            try:
                cursor.execute(request, (phone_number,))
                self.conn.commit()
                print(f'Phone {phone_number} was deleted.')
                sleep(1)
            except(Exception, psycopg2.Error) as error:
                print(f"Error deleting phone: {error}")
                sleep(1)

    def delete_client(self, client):
        with self.conn.cursor() as cursor:
            request = '''
                       DELETE FROM client
                       WHERE client_id = %s
                      '''
            try:
                cursor.execute(request, (client[0],))
                self.conn.commit()
                print(f'Client {client[2]} {client[1]} was deleted.')
                sleep(1)
            except(Exception, psycopg2.Error) as error:
                print(f"Error deleting client: {error}")
                sleep(1)

    def find_client(self, email):
        with self.conn.cursor() as cursor:
            request = '''
                SELECT 
                    client_id, 
                    name, 
                    surname, 
                    email, 
                    ARRAY_TO_STRING((select array(select number 
                                                  from phones)
                                                  ), ', ') phones
                FROM client
                WHERE email = %s
                '''
            cursor.execute(request, (email,))
            return cursor.fetchone()


def main_loop(conn):

    while True:
        print('''
        CHOOSE NUMBER OF OPTION TO EXECUTE:
        1. Create tables (if not created);
        2. Add new client;
        3. Add phone number to existed client;
        4. Update client;
        5. Delete number from client;
        6. Delete client;
        7. Find client;
        0. Exit;
        ''')
        command = input('What you want to do? ')
        # Exit
        if command == '0':
            break

        # Create base tables
        elif command == '1':
            try:
                conn.create_tables()
                print('Tables created successfully')
                sleep(1)
            except(Exception, psycopg2.Error) as error:
                print(f"Error creating table: {error}")
                sleep(1)

        # Create new clients
        elif command == '2':
            name = input('Name: ').strip().capitalize()
            surname = input('Surname: ').strip().capitalize()
            email = input('Email: ').strip()
            try:
                emailinfo = validate_email(email, check_deliverability=False)
                email = emailinfo.normalized
            except EmailNotValidError as e:
                print(str(e))
                sleep(1)
                continue
            conn.add_client(name, surname, email)

        # Add phone numbers
        elif command == '3':
            email = input('Enter email of existed client: ').strip()
            email = check_email(email)
            if not email:
                continue
            client = conn.find_client(email)
            if not client:
                print(f'Client with email: {email} not found.')
                sleep(1)
                continue
            client_id = client[0]
            phone = input('Enter phone number: ')
            conn.add_phone_number(client_id, phone)

        # Edit clients
        elif command == '4':
            email = input('Enter email of existed client: ').strip()
            email = check_email(email)
            if not email:
                continue
            client = conn.find_client(email)
            if not client:
                print(f'Client with email: {email} not found.')
                sleep(1)
                continue
            client_id = client[0]
            while True:
                print(f'''
                ----------------------------------------------------------
                Found client: Name: {client[1]}
                              Surname: {client[2]}
                ----------------------------------------------------------
                WHAT YOU WANT TO CHANGE:
                1. Name;
                2. Surname;
                3. E-mail;
                0. Go back;
                ''')
                change_id = int(input('Enter a command id: '))
                if change_id not in (1, 2, 3, 0):
                    print('Need a number between 0 and 3')
                    continue
                elif change_id == 0:
                    break
                elif change_id == 1:
                    to_change = 'name'
                    new_value = input('Enter new name: ').strip().capitalize()
                elif change_id == 2:
                    to_change = 'surname'
                    new_value = input('Enter new surname: ').strip().capitalize()
                elif change_id == 3:
                    to_change = 'email'
                    new_value = input('Enter new email: ')
                    email = check_email(new_value)
                    if not email:
                        continue
                conn.update_client(client_id, to_change, new_value)

        # Delete phone numbers
        elif command == '5':
            phone = input('Enter phone number to delete: ').strip()
            suggest = input(f' Deleting phone number: {phone}. ARE YOU SURE? y/n: ')
            if suggest.lower() in ('y', 'yes', 1):
                conn.delete_number(phone)

        # Delete clients
        elif command == '6':
            email = input('Enter email of existed client: ').strip()
            email = check_email(email)
            if not email:
                continue
            client = conn.find_client(email)
            if not client:
                print(f'Client with email: {email} not found.')
                sleep(1)
                continue
            suggest = input(f' Deleting: {client[1]} {client[2]}. ARE YOU SURE? y/n: ')
            if suggest.lower() in ('y', 'yes', 1):
                conn.delete_client(client)


        # Find clients
        elif command == '7':
            email = input('Enter email of existed client: ').strip()
            email = check_email(email)
            if not email:
                continue
            client = conn.find_client(email)
            if not client:
                print(f'Client with email: {email} not found.')
                sleep(1)
                continue
            print(f'''
           ----------------------------------------------------------
           Found client: Name: {client[1]}
                         Surname: {client[2]}
                         Email: {client[3]}
                         Phones: {client[4]}
           ----------------------------------------------------------
           ''')
            input('--Press any button to continue--')


def check_email(email: str):
    try:
        emailinfo = validate_email(email, check_deliverability=False)
        return emailinfo.normalized
    except EmailNotValidError as e:
        print(str(e))
        sleep(1)
        return


if __name__ == '__main__':
    conn = Connector('psql_from_python', 'postgres', '167wq%t')
    conn.connect()
    main_loop(conn)
    conn.close_connection()
