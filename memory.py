from langchain.memory import ConversationBufferWindowMemory
from config import setup_logging, get_db_creds
from pymongo import MongoClient
from bson.binary import Binary
import pickle
from datetime import datetime, timedelta
from pymongo import MongoClient

# Get MongoDB credentials
MONGODB_URI, MONGODB_DB_NAME = get_db_creds()

# Set up logging
logger = setup_logging()

# Initialize MongoDB collections
try:
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]
    memories = db['memories']
    locks = db['locks']
    logger.info('Successfully connected to MongoDB.')
except Exception as e:
    logger.error('Failed to connect to MongoDB.', exc_info=True)
    raise e

def acquire_lock(username):
    # Current time
    now = datetime.utcnow()

    # Try to acquire the lock
    result = locks.find_one({'_id': username})
    if result is None or ('expire_at' in result and result['expire_at'] < now):
        # If the lock doesn't exist or has expired, it can be acquired
        locks.update_one(
            {'_id': username},
            {'$set': {'expire_at': now + timedelta(seconds=60)}},
            upsert=True
        )
        return True
    else:
        return False

def release_lock(username):
    # Release the lock
    locks.delete_one({'_id': username})

class LockManager:
    def __init__(self, username):
        self.username = username

    def __enter__(self):
        if not acquire_lock(self.username):
            raise Exception(f'User {self.username} is currently locked.')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        release_lock(self.username)

def get_user_memory(username):
    with LockManager(username):
        try:
            # Fetch memory from the database
            memory_doc = memories.find_one({'username': username})

            if memory_doc is None:
                logger.info(f'Initializing memory for user {username}...')

                # Create a new index for this user
                memory = ConversationBufferWindowMemory(k=4, memory_key='chat_history', return_messages=False)

                # Store this user's memory in MongoDB
                memory_blob = Binary(pickle.dumps(memory))
                memories.insert_one({'username': username, 'memory': memory_blob})

                logger.info(f'Successfully Initialized memory for user {username}')
            else:
                # Load memory from the database
                memory = pickle.loads(memory_doc['memory'])

            return memory
    
        except Exception as e:
            logger.error(f'Failed to get memory for user {username}.', exc_info=True)
            raise e

def save_user_memory(username, memory):
    with LockManager(username):
        try:
            # Update the user's memory in MongoDB
            memory_blob = Binary(pickle.dumps(memory))
            memories.update_one({'username': username}, {'$set': {'memory': memory_blob}}, upsert=True)
            logger.info(f'Successfully saved memory for user {username}')
        except Exception as e:
            logger.error(f'Failed to save memory for user {username}.', exc_info=True)
            raise e
