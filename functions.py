import os
import time
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta


# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGODB_URI")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MongoDB connection
try:
    client = MongoClient(MONGO_URI)
    db = client.get_database("smmhubboosterv2")
    users_collection = db.users
    orders_collection = db.orders
    logger.info("Connected to MongoDB successfully")
except PyMongoError as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

def isExists(user_id):
    """Check if the user exists in database."""
    try:
        return users_collection.count_documents({"user_id": str(user_id)}) > 0
    except PyMongoError as e:
        logger.error(f"Error checking user existence {user_id}: {e}")
        return False

def insertUser(user_id, data):
    """Insert user data if user doesn't exist."""
    try:
        user_id = str(user_id)
        
        # Ensure balance is stored as float, not string
        if 'balance' in data:
            data['balance'] = float(data['balance'])
        
        # Add default fields for new users
        data['user_id'] = user_id
        data['join_date'] = data.get('join_date', datetime.now())  # Add join_date if not provided
        data['total_deposits'] = data.get('total_deposits', 0.0)  # Default total deposits
        data['orders_count'] = data.get('orders_count', 0)  # Default order count
        data['total_refs'] = data.get('total_refs', 0)  # Default referral count
        data['welcome_bonus'] = data.get('welcome_bonus', 0)  # Default welcome bonus status
        data['referred'] = data.get('referred', 0)  # Default referral status
        data['banned'] = data.get('banned', False)  # Default banned status
        
        # Insert the user into the database
        result = users_collection.insert_one(data)
        return result.inserted_id is not None
    except PyMongoError as e:
        logger.error(f"Error inserting user {user_id}: {e}")
        return False

def getData(user_id):
    """Retrieve all user data."""
    try:
        user_data = users_collection.find_one({"user_id": str(user_id)}, {'_id': 0})
        if user_data and 'balance' in user_data:
            # Ensure balance is returned as float
            user_data['balance'] = float(user_data['balance'])
        return user_data or None
    except PyMongoError as e:
        logger.error(f"Error getting user data {user_id}: {e}")
        return None

def updateUser(user_id, data):
    """Update user data in the database."""
    try:
        user_id = str(user_id)
        result = users_collection.update_one(
            {"user_id": user_id},
            {"$set": data},
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None
    except PyMongoError as e:
        logger.error(f"Error updating user {user_id}: {e}")
        return False

def addBalance(user_id, amount):
    """Add balance to the user account and track deposits"""
    try:
        user_id = str(user_id)
        amount = float(amount)
        
        # Update both balance and total_deposits
        result = users_collection.update_one(
            {"user_id": user_id},
            {
                "$inc": {
                    "balance": amount,
                    "total_deposits": amount  # Track deposits separately
                }
            },
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None
    except (PyMongoError, ValueError) as e:
        logger.error(f"Error adding balance for {user_id}: {e}")
        return False

def cutBalance(user_id, amount):
    """Deduct balance from the user account (doesn't affect total_deposits)"""
    try:
        user_id = str(user_id)
        amount = float(amount)
        
        user = users_collection.find_one({"user_id": user_id})
        if not user:
            return False
            
        if float(user.get('balance', 0)) >= amount:
            result = users_collection.update_one(
                {"user_id": user_id},
                {"$inc": {"balance": -amount}}
            )
            return result.modified_count > 0
        return False
    except (PyMongoError, ValueError) as e:
        logger.error(f"Error cutting balance for {user_id}: {e}")
        return False

def track_exists(user_id):
    """Check if the referral user exists."""
    return isExists(user_id)

def setWelcomeStaus(user_id):
    """Set the welcome bonus status for the user."""
    try:
        user_id = str(user_id)
        result = users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"welcome_bonus": 1}}
        )
        return result.modified_count > 0
    except PyMongoError as e:
        logger.error(f"Error setting welcome status for {user_id}: {e}")
        return False

def setReferredStatus(user_id):
    """Set the referral status for the user."""
    try:
        user_id = str(user_id)
        result = users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"referred": 1}}
        )
        return result.modified_count > 0
    except PyMongoError as e:
        logger.error(f"Error setting referred status for {user_id}: {e}")
        return False

def addRefCount(user_id):
    """Increment the referral count for the user."""
    try:
        user_id = str(user_id)
        result = users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"total_refs": 1}}
        )
        return result.modified_count > 0
    except PyMongoError as e:
        logger.error(f"Error adding referral count for {user_id}: {e}")
        return False

def add_order(user_id, order_data):
    """Add a new order to user's history."""
    try:
        order_data['user_id'] = str(user_id)
        if 'timestamp' not in order_data:
            order_data['timestamp'] = time.time()
        if 'status' not in order_data:
            order_data['status'] = 'pending'
        
        # Insert into orders collection
        result = orders_collection.insert_one(order_data)
        
        # Update user's order count (create field if doesn't exist)
        users_collection.update_one(
            {"user_id": str(user_id)},
            {"$inc": {"orders_count": 1}},
            upsert=True
        )
        
        return result.inserted_id is not None
    except PyMongoError as e:
        logger.error(f"Error adding order for {user_id}: {e}")
        return False

def update_order_status(user_id, order_id, new_status):
    """Update status of a specific order."""
    try:
        result = orders_collection.update_one(
            {"user_id": str(user_id), "order_id": order_id},
            {"$set": {
                "status": new_status,
                "status_update_time": time.time()
            }}
        )
        return result.modified_count > 0
    except PyMongoError as e:
        logger.error(f"Error updating order status {order_id}: {e}")
        return False

def get_user_orders_stats(user_id):
    """Get order statistics for a specific user."""
    stats = {
        'total': 0,
        'completed': 0,
        'pending': 0,
        'failed': 0
    }
    
    try:
        # Get counts for each status
        pipeline = [
            {"$match": {"user_id": str(user_id)}},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]
        
        results = list(orders_collection.aggregate(pipeline))
        
        # Initialize all counts to 0 first
        stats = {
            'total': 0,
            'completed': 0,
            'pending': 0,
            'failed': 0
        }
        
        # Update counts based on aggregation results
        for result in results:
            status = result["_id"].lower()
            if status in stats:
                stats[status] = result["count"]
        
        # Calculate total as sum of all status counts
        stats['total'] = stats['completed'] + stats['pending'] + stats['failed']
        
    except Exception as e:  # Changed from PyMongoError to Exception for broader coverage
        logger.error(f"Error getting order stats for {user_id}: {e}")
        # Return default stats with all zeros if there's an error
    
    return stats

# Admin functions
def get_all_users():
    """Get list of all user IDs"""
    try:
        return [user['user_id'] for user in users_collection.find({}, {'user_id': 1, '_id': 0})]
    except PyMongoError as e:
        logger.error(f"Error getting all users: {e}")
        return []

def get_user_count():
    """Get total number of users"""
    try:
        return users_collection.count_documents({})
    except PyMongoError as e:
        logger.error(f"Error getting user count: {e}")
        return 0

def ban_user(user_id):
    """Ban a user by setting banned flag"""
    try:
        user_id = str(user_id)
        result = users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"banned": True}},
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None
    except PyMongoError as e:
        logger.error(f"Error banning user {user_id}: {e}")
        return False

def unban_user(user_id):
    """Unban a user by removing banned flag"""
    try:
        user_id = str(user_id)
        result = users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"banned": False}}
        )
        return result.modified_count > 0
    except PyMongoError as e:
        logger.error(f"Error unbanning user {user_id}: {e}")
        return False

def is_banned(user_id):
    """Check if user is banned"""
    try:
        user = users_collection.find_one(
            {"user_id": str(user_id)},
            {"banned": 1}
        )
        return user and user.get("banned", False)
    except PyMongoError as e:
        logger.error(f"Error checking ban status for {user_id}: {e}")
        return False

def get_banned_users():
    """Get list of all banned user IDs"""
    try:
        return [user['user_id'] for user in users_collection.find(
            {"banned": True},
            {'user_id': 1, '_id': 0}
        )]
    except PyMongoError as e:
        logger.error(f"Error getting banned users: {e}")
        return []

def get_top_users(limit=10):
    """Get top users by order count"""
    try:
        pipeline = [
            {"$group": {
                "_id": "$user_id",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        return [(str(item["_id"]), item["count"]) for item in orders_collection.aggregate(pipeline)]
    except PyMongoError as e:
        logger.error(f"Error getting top users: {e}")
        return []

def get_active_users(days=7):
    """Get count of users active in last X days"""
    try:
        cutoff = time.time() - (days * 24 * 60 * 60)
        return users_collection.count_documents({
            "last_activity": {"$gte": cutoff}
        })
    except PyMongoError as e:
        logger.error(f"Error getting active users: {e}")
        return 0

def get_total_orders():
    """Get total orders processed"""
    try:
        return orders_collection.count_documents({})
    except PyMongoError as e:
        logger.error(f"Error getting total orders: {e}")
        return 0

def get_total_deposits():
    """Get total coins added by admin (not affected by spending)"""
    try:
        # Track deposits separately in user document
        result = users_collection.aggregate([{
            "$group": {
                "_id": None,
                "total": {"$sum": "$total_deposits"}
            }
        }])
        return next(result, {"total": 0})["total"]
    except PyMongoError as e:
        logger.error(f"Error getting total deposits: {e}")
        return 0

def get_top_referrer():
    """Get user with most referrals"""
    try:
        result = users_collection.find_one(
            {"total_refs": {"$gt": 0}},
            {"user_id": 1, "username": 1, "total_refs": 1},
            sort=[("total_refs", -1)]
        )
        if result:
            return {
                'user_id': result.get('user_id'),
                'username': result.get('username', 'N/A'),
                'count': result.get('total_refs', 0)
            }
        return {'user_id': None, 'username': None, 'count': 0}
    except PyMongoError as e:
        logger.error(f"Error getting top referrer: {e}")
        return {'user_id': None, 'username': None, 'count': 0}

def get_completed_orders():
    """Get the total number of completed orders."""
    try:
        return orders_collection.count_documents({"status": "completed"})
    except PyMongoError as e:
        logger.error(f"Error getting completed orders: {e}")
        return 0


def get_new_users(days=1):
    """Get the number of new users who joined within the last `days`."""
    try:
        # Calculate the cutoff date
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Query the database for users who joined after the cutoff date
        return users_collection.count_documents({"join_date": {"$gte": cutoff_date}})
    except PyMongoError as e:
        logger.error(f"Error getting new users: {e}")
        return 0

# -- Pinned messages MongoDB -- #

def save_pinned_message(user_id, message_id):
    """Save pinned message ID for a user"""
    try:
        users_collection.update_one(
            {"user_id": str(user_id)},
            {"$set": {"pinned_message_id": message_id}},
            upsert=True
        )
    except Exception as e:
        print(f"Error saving pinned message for {user_id}: {e}")

def get_all_pinned_messages():
    """Get all users with pinned message IDs"""
    pinned = {}
    try:
        users = users_collection.find({"pinned_message_id": {"$exists": True}})
        for user in users:
            pinned[user['user_id']] = user['pinned_message_id']
    except Exception as e:
        print(f"Error loading pinned messages: {e}")
    return pinned

def clear_all_pinned_messages():
    """Clear pinned message IDs from all users"""
    try:
        users_collection.update_many(
            {"pinned_message_id": {"$exists": True}},
            {"$unset": {"pinned_message_id": ""}}
        )
    except Exception as e:
        print(f"Error clearing pinned messages: {e}")


print("functions.py loaded with MongoDB support")
