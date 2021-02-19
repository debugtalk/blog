import unittest

class Node(object):
    def __init__(self, data, next_node=None):
        self.data = data
        self.next_node = next_node


def create_linked_list(lst):
    head = None

    for data in lst:
        head = Node(data, head)

    return head

def traverse_linked_list(head):
    probe = head
    lst = []
    while probe is not None:
        lst.append(probe.data)
        probe = probe.next_node
    return lst

def insert_item_by_value(head, pre_value, value):
    probe = head
    while probe is not None:
        if probe.data == pre_value:
            # found pre_value
            new_node = Node(value, None)
            new_node.next_node = probe.next_node
            probe.next_node = new_node
            return 0

        if probe.next_node is not None:
            # probe is not last, continue search
            probe = probe.next_node
        else:
            # probe is last and pre_value is not found
            print("{} is not exist".format(pre_value))
            return -1

def delete_item_by_value(head, pre_value):
    probe = head
    while probe is not None:
        if probe.data != pre_value:
            # continue
            probe = probe.next_node
            continue

        # found pre_value
        if probe.next_node is None:
            # pre_value is last item
            probe = None
        # else:
        #     # pre_value is not last item



class TestLinkedList(unittest.TestCase):

    def setUp(self):
        self.head = create_linked_list(range(1,6))

    def test_create_linked_list(self):
        self.assertEqual(
            traverse_linked_list(self.head),
            [5, 4, 3, 2, 1]
        )

    def test_insert_item_by_value_middle(self):
        # insert in the middle
        insert_item_by_value(self.head, 3, 20)
        self.assertEqual(
            traverse_linked_list(self.head),
            [5, 4, 3, 20, 2, 1]
        )

    def test_insert_item_by_value_after_last(self):
        # insert after last
        insert_item_by_value(self.head, 1, 20)
        self.assertEqual(
            traverse_linked_list(self.head),
            [5, 4, 3, 2, 1, 20]
        )

    def test_insert_item_by_value_not_found(self):
        # item not found
        self.assertEqual(
            insert_item_by_value(self.head, 6, 8),
            -1
        )
        self.assertEqual(
            traverse_linked_list(self.head),
            [5, 4, 3, 2, 1]
        )

    def test_delete_item_by_value_last(self):
        delete_item_by_value(self.head, 1)
        self.assertEqual(
            traverse_linked_list(self.head),
            [5, 4, 3, 2]
        )


if __name__ == "__main__":
    unittest.main()
