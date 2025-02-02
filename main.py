from collections import UserDict
from datetime import datetime, timedelta
import pickle
from abc import ABC, abstractmethod

class BaseView(ABC):
    @abstractmethod
    def display_contacts(self, book):
        pass

    @abstractmethod
    def display_message(self, message: str):
        pass

    @abstractmethod
    def display_help(self):
        pass


class ConsoleView(BaseView):
    def display_contacts(self, book):
        print("Contacts:")
        if not book.data:
            print("No contacts found.")
        else:
            print("\n".join(str(record) for record in book.data.values()))

    def display_message(self, message: str):
        print(message)

    def display_help(self):
        print(
            """Available commands:
    add [name] [phone] - Add a new contact or update an existing one.
    change [name] [old_phone] [new_phone] - Change the phone number of a contact.
    phone [name] - Show the phone numbers of a contact.
    all - Show all contacts.
    add-birthday [name] [birthday] - Add a birthday to a contact.
    show-birthday [name] - Show the birthday of a contact.
    birthdays - Show upcoming birthdays within 7 days.
    hello - Get a greeting from the bot.
    close or exit - Exit the program."""
        )


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):  # Class for storing contact name.
    def __init__(self, value):
        super().__init__(value)


class Phone(Field):  # Class for storing phone numbers.
    def __init__(self, value):
        if len(value) == 10 and value.isdigit():  # Format validation (10 digits).
            super().__init__(value)
        else:
            raise ValueError


class Birthday(Field):
    def __init__(self, value):
        try:
            datetime.strptime(value, "%d.%m.%Y")  # Тільки перевірка формату
            super().__init__(value)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):  # Method for adding.
        self.phones.append(Phone(phone))

    def find_phone(self, phone):  # Method for finding Phone objects.
        for phone_obj in self.phones:
            if phone_obj.value == phone:
                return phone_obj
        return None

    def remove_phone(self, phone):  # Method for removal.
        self.phones.remove(self.find_phone(phone))

    def edit_phone(self, old_phone, new_phone):  # Method for editing.
        if self.find_phone(old_phone):  # If the old_phone exists and the new_phone is valid.
            self.add_phone(new_phone)
            self.remove_phone(old_phone)
        else:
            raise ValueError

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        birthday = f", birthday: {self.birthday.value}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}{birthday}"


class AddressBook(UserDict):
    def add_record(self, record):  # Method that adds a record to "self.data".
        self.data[record.name.value] = record

    def find(self, name):  # Method that finds a record by name.
        return self.data.get(name)

    def delete(self, name):  # Method that deletes a record by name.
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):
        upcoming_birthdays = []
        today = datetime.today().date()

        for record in self.data.values():
            if record.birthday:
                birthday_date = datetime.strptime(record.birthday.value, "%d.%m.%Y").date()
                birthday_this_year = birthday_date.replace(year=today.year)

                if birthday_this_year < today:
                    birthday_this_year = birthday_date.replace(year=today.year + 1)

                if 0 <= (birthday_this_year - today).days <= 7:
                    congratulation_date = birthday_this_year
                    if congratulation_date.weekday() >= 5:
                        congratulation_date += timedelta(days=(7 - congratulation_date.weekday()))
                    upcoming_birthdays.append(
                        {"name": record.name.value, "birthday": congratulation_date.strftime("%d.%m.%Y")})
        return upcoming_birthdays

    def __str__(self):
        return "\n".join(str(record) for record in self.data.values())


def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError:
            return "Give me corect data please."
        except IndexError:
            return "Enter user name please"
        except KeyError:
            return "Contact not found"
        except Exception as e:
            return f"Помилка: {e}"

    return inner


@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        if not phone in [phone.value for phone in record.phones]:
            record.add_phone(phone)
    return message


@input_error
def change_contact(args, book):
    name, old_phone, new_phone = args
    record = book.find(name)
    if record:
        record.edit_phone(old_phone, new_phone)
        return f"Phone number for {name} changed from {old_phone} to {new_phone}."
    return "Contact not found."


@input_error
def show_phone(args, book):
    name = args[0]
    record = book.find(name)
    if record:
        phones = "; ".join(phone.value for phone in record.phones)
        return f"{name}'s phones: {phones}" if phones else f"{name} has no phone numbers."
    return "Contact not found."


@input_error
def add_birthday(args, book):
    name, birthday = args
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        return "Birthday added."
    return "Contact not found."


@input_error
def show_birthday(args, book):
    name = args[0]
    record = book.find(name)
    if record and record.birthday:
        return record.birthday.value
    return "Birthday not found for this contact."


@input_error
def birthdays(args, book):
    upcoming = book.get_upcoming_birthdays()
    if upcoming:
        return "\n".join(f"{b['name']}: {b['birthday']}" for b in upcoming)
    return "No upcoming birthdays."


@input_error
def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args


def main():
    book = load_data()  # Data loading at startup.
    view = ConsoleView()
    view.display_message("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)  # Save data before exiting.
            view.display_message("Good bye!")
            break

        elif command == "hello":
            view.display_message("How can I help you?")

        elif command == "add":
            view.display_message(add_contact(args, book))

        elif command == "change":
            view.display_message(change_contact(args, book))

        elif command == "phone":
            view.display_message(show_phone(args, book))

        elif command == "all":
            view.display_contacts(book)

        elif command == "add-birthday":
            view.display_message(add_birthday(args, book))

        elif command == "show-birthday":
            view.display_message(show_birthday(args, book))

        elif command == "birthdays":
            view.display_message(birthdays(args, book))

        elif command == "help":
            view.display_help()

        else:
            view.display_message("Invalid command.")


if __name__ == "__main__":
    main()