from django.db import connection
from django.contrib.auth.models import User
from base.models import ExpenseGroup, GroupMember 
from django.db import models
from datetime import datetime
from decimal import Decimal

def build_group_summary(user):
    """
    Build a comprehensive group summary for a user including all groups they're part of
    Returns a list of groups with all expenses and member details
    """
    with connection.cursor() as cursor:
        # Get all groups the user is part of (either created by them or they're a member)
        cursor.execute("""
            SELECT DISTINCT g.id, g.name, g.created_by_id, g.created_at
            FROM base_expensegroup g
            LEFT JOIN base_groupmember gm ON g.id = gm.group_id
            WHERE g.created_by_id = %s OR gm.user_id = %s
            ORDER BY g.created_at DESC
        """, [user.id, user.id])
        
        groups = cursor.fetchall()
        group_summaries = []
        
        for group_id, group_name, created_by_id, created_at in groups:
            # Get group creator information
            cursor.execute("""
                SELECT username, first_name, last_name
                FROM auth_user
                WHERE id = %s
            """, [created_by_id])
            
            creator_data = cursor.fetchone()
            creator_name = f"{creator_data[1]} {creator_data[2]}".strip() or creator_data[0]
            
            # Get total group expense
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) as total_expense
                FROM base_groupexpense
                WHERE group_id = %s
            """, [group_id])
            
            total_expense = cursor.fetchone()[0]
            
            # Get member count
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) as member_count
                FROM base_groupmember
                WHERE group_id = %s
            """, [group_id])
            
            member_count = cursor.fetchone()[0]
            
            # Calculate user's balance in this group
            user_balance = _calculate_user_balance(cursor, group_id, user.id)
            # Get expenses for this group
            expenses = _get_group_expenses(cursor, group_id)
            
            # Get members list with their balances
            members_list = _get_group_members_with_balances(cursor, group_id)
            memebers_sepding = _get_group_members_with_sepding(group_id)
            
            
            group_summary = {
                'id': group_id,
                'name': group_name,
                'totalExpense': float(total_expense) if total_expense else 0.0,
                'userBalance': float(user_balance),
                'members': member_count,
                'createdBy': creator_name,
                'expenses': expenses,
                'membersList': members_list,
                'membersSpending': memebers_sepding 
            }
            
            #now adding total_spending_on_users in group
            
            group_summaries.append(group_summary)
    
    return group_summaries

def get_group_detail(group_id,user_id):
    """
    Get detailed information for a specific group
    Returns a single group object with all expenses and member details
    """
    with connection.cursor() as cursor:
        # Get basic group information
        cursor.execute("""
            SELECT 
                g.id,
                g.name,
                g.created_by_id,
                g.created_at,
                u.username,
                u.first_name,
                u.last_name
            FROM base_expensegroup g
            JOIN auth_user u ON g.created_by_id = u.id
            WHERE g.id = %s
        """, [group_id])
        
        group_data = cursor.fetchone()
        
        if not group_data:
            return None  # Group not found
        
        group_id, name, created_by_id, created_at, creator_username, creator_first, creator_last = group_data
        creator_name = f"{creator_first} {creator_last}".strip() or creator_username
        
        # Get total group expense
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) as total_expense
            FROM base_groupexpense
            WHERE group_id = %s
        """, [group_id])
        
        total_expense = cursor.fetchone()[0]
        
        # Get member count
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) as member_count
            FROM base_groupmember
            WHERE group_id = %s
        """, [group_id])
        
        member_count = cursor.fetchone()[0]
        
        # Get expenses and members
        expenses = _get_group_expenses(cursor, group_id)
        members_list = _get_group_members_with_balances(cursor, group_id)
        memebers_sepding = _get_group_members_with_sepding(group_id)
        
        group_detail = {
            'id': group_id,
            'name': name,
            'userBalance': _calculate_user_balance(cursor, group_id, user_id),#only 2 value after . in am
            'totalExpense': float(total_expense) if total_expense else 0.0,
            'members': member_count,
            'createdBy': creator_name,
            'expenses': expenses,
            'membersList': members_list,
            'membersSpending': memebers_sepding # why this
        }

        return group_detail

def _calculate_user_balance(cursor, group_id, user_id):
    """
    Calculate how much a user is owed (+) or owes (-) in a group
    """
    # Amount user has paid
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) as total_paid
        FROM base_groupexpense
        WHERE group_id = %s AND paid_by_id = %s
    """, [group_id, user_id])
    
    total_paid = cursor.fetchone()[0]
    
    # Amount user owes (their share of all expenses)
    cursor.execute("""
        SELECT COALESCE(SUM(ges.share_amount), 0) as total_owed
        FROM base_groupexpenseshare ges
        JOIN base_groupexpense ge ON ges.expense_id = ge.id
        WHERE ge.group_id = %s AND ges.participant_id = %s
    """, [group_id, user_id])
    
    total_owed = cursor.fetchone()[0]
    
    # Balance = what they paid - what they owe
    # Positive means they are owed money, negative means they owe money
    # two digits after decimal
    return round(float(total_paid) - float(total_owed), 2)

def _get_group_expenses(cursor, group_id):
    """
    Get all expenses for a group with detailed information
    """
    cursor.execute("""
        SELECT 
            ge.id,
            ge.title,
            ge.amount,
            ge.paid_on,
            u.username,
            u.first_name,
            u.last_name
        FROM base_groupexpense ge
        LEFT JOIN auth_user u ON ge.paid_by_id = u.id
        WHERE ge.group_id = %s
        ORDER BY ge.paid_on DESC
    """, [group_id])
    
    expenses_data = cursor.fetchall()
    expenses = []
    
    for exp_id, title, amount, paid_on, username, first_name, last_name in expenses_data:
        # Get who paid for this expense
        paid_by_name = f"{first_name} {last_name}".strip() or username
        
        # Get participants for this expense
        cursor.execute("""
            SELECT 
                u.username,
                u.first_name,
                u.last_name
            FROM base_groupexpenseshare ges
            JOIN auth_user u ON ges.participant_id = u.id
            WHERE ges.expense_id = %s
            ORDER BY u.first_name, u.last_name
        """, [exp_id])
        
        participants_data = cursor.fetchall()
        split_between = []
        
        for p_username, p_first_name, p_last_name in participants_data:
            participant_name = f"{p_first_name} {p_last_name}".strip() or p_username
            split_between.append(participant_name)
        
        expense = {
            'id': exp_id,
            'title': title,
            'amount': float(amount),
            'paidBy': paid_by_name,
            'splitBetween': split_between,
            'date': paid_on.strftime('%Y-%m-%d') if paid_on else None
        }
        
        expenses.append(expense)
    
    return expenses


def _get_group_members_with_balances(cursor, group_id):
    """
    Get all members of a group with their current balances
    """
    cursor.execute("""
        SELECT 
            u.id,
            u.username,
            u.first_name,
            u.last_name
        FROM base_groupmember gm
        JOIN auth_user u ON gm.user_id = u.id
        WHERE gm.group_id = %s
        ORDER BY u.first_name, u.last_name
    """, [group_id])
    
    members_data = cursor.fetchall()
    members_list = []
    
    for member_id, username, first_name, last_name in members_data:
        member_name = f"{first_name} {last_name}".strip() or username
        
        # Calculate balance for this member
        balance = _calculate_user_balance(cursor, group_id, member_id)
        
        member = {
            'id':member_id,
            'name': member_name,
            'balance': float(balance)
        }
        
        members_list.append(member)
    
    return members_list


def get_total_spending_on_user(user_id=None, group_id=None):
    
    user  = User.objects.get(id=user_id)  
    group = ExpenseGroup.objects.get(id=group_id)
    
    res =  user.expense_shares.filter(expense__group=group).aggregate(
        total_spending=models.Sum('share_amount')
    )['total_spending']
    
    return res if res is not None else Decimal('0.00')
  
    
    # Assuming there's a related name for expenses in the ExpenseGroup model
   
def _get_group_members_with_sepding(group_id):
    memberd_spending_list = []
    members= GroupMember.objects.filter(group_id=group_id)
    for mem in members:
        total = get_total_spending_on_user(mem.user.id, group_id)
        member = {
            'id': mem.user.id,
            'name': mem.user.username,
            'total_spending': total
        }
        memberd_spending_list.append(member)
    return memberd_spending_list
        
        
        # user_id ,username = User.