from datetime import timedelta
import re
from apps.email_manager.models import EmailData
import re

from apps.email_manager.models.email import EmailAttachment
from os import path
from django.db.models import Q
# what is the longest length of convo
# how to extract one conversations from the data

class EmailNode:
    def __init__(self, previous_node, email_data, next_node):
        self.previous_node: EmailNode = previous_node
        self.email_data: EmailData = email_data
        self.next_node: EmailNode = next_node

class EmailConvo:
    def __init__(self, first_email):
        email_node = EmailNode(
            previous_node=None,
            email_data=first_email,
            next_node=None
        )
        self.head_email_node = email_node
        self.tail_email_node = email_node
        self.root_dir = "/Users/mirbilal/Desktop/minsir/"
    
    def append_email_node_to_convo(self, new_email):
        next_node = EmailNode(
            previous_node=self.tail_email_node,
            email_data=new_email,
            next_node=None
        )
        self.tail_email_node.next_node = next_node
        self.tail_email_node = next_node

    def prepend_email_node_to_convo(self, new_email):
        first_node = EmailNode(
            previous_node=None,
            email_data=new_email,
            next_node=self.head_email_node
        )
        self.head_email_node.previous_node = first_node
        self.head_email_node = first_node

    def remove_last_email(self):
        new_last_email = self.tail_email_node.previous_node
        if new_last_email is not None:
            new_last_email.next_node = None
            self.tail_email_node = new_last_email

    def remove_first_email(self):
        new_first_email = self.head_email_node.next_node
        if new_first_email is not None:
            new_first_email.previous_node = None
            self.head_email_node = new_first_email
    
    def remove_email_from_convo(self, index = None, e_id = None):
        if (index is not None and id is not None) or (index is None and id is None):
            return -1
        iter = 0
        def _remove_email_from_convo(current_node: EmailNode):
            nonlocal iter
            if (e_id is not None and current_node.email_data.id == e_id) or (index is not None and iter==index):
                previous_node: EmailNode = current_node.previous_node
                next_node: EmailNode = current_node.next_node
                if previous_node is not None and next_node is not None:
                    previous_node.next_node = next_node
                    next_node.previous_node = previous_node
                elif previous_node is not None and next_node is None:
                    previous_node.next_node = None
                elif previous_node is None and next_node is not None:
                    next_node.previous_node = None
                    self.head_email_node = next_node
                elif previous_node is None and next_node is None:
                    return 0
                return 1
            else:
                next_node = current_node.next_node
                if next_node is not None:
                    iter = iter + 1
                    return _remove_email_from_convo(next_node)
                else:
                    return -1
        return _remove_email_from_convo(self.head_email_node)
    
    def insert_email_into_convo(self, new_email: EmailData, index = None, e_id = None):
        if (index is not None and id is not None) or (index is None and id is None):
            return -1
        iter = 0
        def _insert_email_into_convo(current_node: EmailNode):
            nonlocal iter
            if (e_id is not None and current_node.email_data.id == e_id) or (index is not None and iter==index):
                new_email_node = EmailNode(
                    previous_node=None,
                    email_data=new_email,
                    next_node=None
                )
                previous_node: EmailNode = current_node.previous_node
                next_node: EmailNode = current_node.next_node
                if previous_node is not None:
                    previous_node.next_node = new_email_node
                    new_email_node.previous_node = previous_node

                    current_node.previous_node = new_email_node
                    new_email_node.next_node = current_node

                else:
                    current_node.previous_node = new_email_node
                    new_email_node.next_node = current_node
                    self.head_email_node = new_email_node
                return 1
            else:
                next_node = current_node.next_node
                if next_node is not None:
                    iter = iter + 1
                    return _insert_email_into_convo(next_node)
                else:
                    return -1
        return _insert_email_into_convo(self.head_email_node)
    
    def retrieve_email_from_convo(self, index = None, e_id = None, text = None):
        if (index is None and id is None and text is None):
            return -1
        iter = 0
        def _retrieve_email_from_convo(current_node: EmailNode):
            nonlocal iter
            if (
                (e_id is not None and current_node.email_data.id == e_id) 
                or (index is not None and iter==index) 
                or (current_node.email_data.body is not None and text in current_node.email_data.body)
            ):
                return current_node.email_data
            else:
                next_node = current_node.next_node
                if next_node is not None:
                    iter = iter + 1
                    return _retrieve_email_from_convo(next_node)
                else:
                    return None
        return _retrieve_email_from_convo(self.head_email_node)
    
    def get_clean_emails(self, email_strings):

        # Regular expression to extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

        # Initialize an empty list to store the extracted email addresses
        all_emails = []

        # Iterate over each string in the list
        for email_string in email_strings:
            # Find all email addresses in the current string
            emails = re.findall(email_pattern, email_string)
            # Extend the all_emails list with the found email addresses
            all_emails.extend([email.lower() for email in emails])

        # Print the list of all extracted email addresses
        return all_emails
    
    def get_full_convo(self):
        first_email = self.head_email_node
        full_convo = []
        attachments_dict = {}
        all_files = {}
        def _get_full_convo(current_email: EmailNode):
            email_data = current_email.email_data
            full_convo.append({
                "from": self.get_clean_emails([email_data.from_email])[0],
                "to": self.get_clean_emails(email_data.to_emails),
                "date": email_data.date.strftime('%B %d, %Y, %-I:%M %p'),
                "subject": email_data.subject,
                "body": email_data.body
            })
            next_email = current_email.next_node
            attachments: list[EmailAttachment] = email_data.attachments.all()
            for an_attchmnt in attachments:
                if an_attchmnt.name is not None:
                    relative_path = an_attchmnt.file.url.lstrip('/')
                    if ".pdf" in relative_path:
                        attachments_dict[an_attchmnt.id] = path.join(self.root_dir, relative_path)
                    all_files[an_attchmnt.id] = path.join(self.root_dir, relative_path)


            if next_email is not None:
                return _get_full_convo(next_email)
            else:
                return None
        _get_full_convo(first_email)
        
        return (full_convo, list(attachments_dict.values()), list(all_files.values()))
    
# if it is of the form re, but before the re, there is one without the re, then split
# create one key for each to email
# check from each


class ConversationReader:
    def __init__(self, start_date, end_date):
        self.conversations = {}
        self.latest_subjects = {}
        self.re_list = [
            "RE: ",
            "Re: ",
            "re: "
        ]
        self.fwd_list = [
            "FW: ",
            "fw: ",
            "Fw: ",
            "FWD: ",
            "Fwd: ",
            "fwd: "
        ]
        self.start_date = start_date
        self.end_date = end_date

    def extract_conversation(self):
        emails = EmailData.objects.filter(
            Q(date__gte = self.start_date)
            &Q(date__lte = self.end_date)
        ).order_by('date').prefetch_related("attachments")
        for an_email in emails:
            email_date = an_email.date
            if an_email.subject and email_date:
                is_reply = False
                is_fwdd = False
                original_subject = an_email.subject.strip()
                
                if any(substring in original_subject for substring in self.re_list):
                    is_reply = True
                if any(substring in original_subject for substring in self.fwd_list):
                    is_fwdd = True
                rmvd_subject = original_subject
                for re_substring in self.re_list:
                    rmvd_subject = rmvd_subject.replace(re_substring, "")
                for fwd_substring in self.fwd_list:
                    rmvd_subject = rmvd_subject.replace(fwd_substring, "")
                rmvd_subject = rmvd_subject.replace("\n", "").replace("\r", "")
                if rmvd_subject in self.latest_subjects:
                    existing_latest_date = self.latest_subjects[rmvd_subject]
                    date_difference = email_date - existing_latest_date
                    if not is_reply and not is_fwdd and date_difference > timedelta(days=30):
                        latest_date = email_date
                        self.latest_subjects[rmvd_subject] = latest_date
                    else:
                        latest_date = self.latest_subjects[rmvd_subject]
                else:
                    latest_date = email_date
                    self.latest_subjects[rmvd_subject] = latest_date
                # if 'RENEWAL | M/S HYGIENE CONTAINERS (PRIVATE) LIMITED | FIRE POLICIES' in rmvd_subject:
                #     print(get_clean_emails([an_email.from_email]))
                #     print(get_clean_emails(an_email.to_emails))
                #     print(original_subject)
                #     print(rmvd_subject)
                #     print("subject in dict", rmvd_subject in self.latest_subjects)
                #     print("is_new ",not is_reply and not is_fwdd and date_difference > timedelta(days=30))
                #     print(email_date.strftime('%B %d, %Y, %-I:%M %p'))
                #     print("")
                formatted_date = latest_date.strftime('%B %d, %Y, %-I:%M %p')
                key_str = f"{formatted_date}@{rmvd_subject}"
                if key_str in self.conversations:
                    convo_emails: EmailConvo = self.conversations[key_str]
                    convo_emails.append_email_node_to_convo(an_email)
                else:
                    self.conversations[key_str] = EmailConvo(first_email=an_email)

            

        
