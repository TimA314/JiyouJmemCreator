#!/usr/bin/env python3
"""
Generate simple conversational dialogue items for english_core curriculum.
Creates 10k+ items covering basic greetings, questions, acknowledgments, etc.
"""

import json
import os
from typing import List, Dict, Any, Set
from itertools import product
import random

# Output directory
LESSONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'curricula', 'english_core.jcur', 'lessons')

# Response pools for variety
GREETING_RESPONSES = [
    "Hello! How can I help you?",
    "Hi there! What can I do for you?",
    "Hello! What's on your mind?",
    "Hi! How can I assist you?",
    "Hello! What would you like to know?",
    "Hey! What's up?",
    "Hey there! How can I help?",
    "Hi! I'm listening.",
    "Hello! Nice to hear from you.",
    "Hey! What brings you here?",
    "Greetings! How may I assist?",
    "Hello! Ready to help!",
    "Hi! What do you need?",
    "Hey! Good to see you!",
    "Hello! I'm here for you.",
    "Hi there! What's going on?",
    "Hey! Let me know how I can help.",
    "Hello! Fire away!",
    "Hi! Ask me anything.",
    "Hey there! What's new?",
]

FAREWELL_RESPONSES = [
    "Goodbye! Take care!",
    "Bye! Have a great day!",
    "See you later!",
    "Take care! Come back anytime.",
    "Goodbye! It was nice chatting.",
    "Bye for now!",
    "See you! Stay well.",
    "Farewell! Until next time.",
    "Bye! Hope to talk again soon.",
    "Goodbye! All the best!",
    "Take care of yourself!",
    "Bye bye! Stay safe!",
    "Catch you later!",
    "See you around!",
    "Goodbye! Don't be a stranger!",
    "Later! Come back soon!",
    "Bye! It was fun!",
    "Farewell friend!",
    "Until we meet again!",
    "Peace out! Take care!",
]

WHATS_UP_RESPONSES = [
    "Not much! What can I help you with?",
    "All good here! What's on your mind?",
    "Just here to help! What do you need?",
    "Ready to assist! What's up with you?",
    "Nothing much! How can I help?",
    "Doing well! What brings you here?",
    "Just chilling! What can I do for you?",
    "All good! What would you like to know?",
    "Hey! Same old, same old. What's up with you?",
    "Just being Jiyou! How about you?",
    "Waiting to hear from you! What's going on?",
    "Ready and waiting! What's new?",
]

HOW_ARE_YOU_RESPONSES = [
    "I'm doing well, thank you! How can I help you?",
    "I'm good, thanks for asking! What's on your mind?",
    "Doing great! How about you?",
    "I'm well! What can I do for you today?",
    "Good! Thanks for asking. How can I assist?",
    "I'm fine, thank you! What brings you here?",
    "Doing okay! What would you like to know?",
    "I'm great! How are you doing?",
    "Pretty good! Thanks for checking in. What's up?",
    "Excellent! What can I help you with?",
    "I'm fantastic! Ready to help!",
    "Wonderful! What do you need?",
]

IDENTITY_RESPONSES = [
    "I'm Jiyou, a spiking neural network AI that thinks and learns differently from traditional AI. How can I help?",
    "I'm Jiyou! I'm an experimental AI built to mimic how biological brains work. What would you like to know?",
    "I'm Jiyou, an AI assistant. I process information through spiking neurons, like a brain. How can I assist you?",
    "My name is Jiyou. I'm an AI that learns through experience, not just pattern matching. What's on your mind?",
    "I'm Jiyou! I'm designed to think more like a brain than traditional AI systems. How can I help?",
    "Jiyou here! I'm an AI with spiking neurons and memory systems. What do you need?",
    "I'm Jiyou, your AI assistant! I learn and grow from our conversations. How can I help?",
    "The name's Jiyou! I'm an experimental spiking neural network. What's up?",
]

CAPABILITY_RESPONSES = [
    "I can help with questions, have conversations, do math, search the web, and more! What do you need?",
    "I can answer questions, chat, help with calculations, look things up, and learn from our conversations. What would you like?",
    "I'm able to have conversations, answer questions, use tools like a calculator and web search. How can I help?",
    "I can chat, answer questions, do calculations, search for information, and remember things you tell me. What's on your mind?",
    "I can assist with many things - questions, math, searches, conversations, and more! What do you need help with?",
    "I'm capable of chatting, calculating, searching, remembering, and learning. What can I do for you?",
]

HELP_RESPONSES = [
    "Of course! What do you need help with?",
    "I'm here to help! What can I do for you?",
    "Sure! Tell me what you need.",
    "Happy to help! What's going on?",
    "I'd be glad to assist! What do you need?",
    "Absolutely! What can I help you with?",
    "Yes! What would you like help with?",
    "I'm ready to help! What's the matter?",
    "Always here to help! What's up?",
    "At your service! What do you need?",
    "Let me help! What's on your mind?",
    "Ready to assist! Tell me more.",
]

THANKS_RESPONSES = [
    "You're welcome!",
    "No problem!",
    "Glad I could help!",
    "Anytime!",
    "Happy to help!",
    "You're welcome! Let me know if you need anything else.",
    "No worries!",
    "My pleasure!",
    "Don't mention it!",
    "Of course! Anything else?",
    "Always happy to help!",
    "You got it!",
]

ACKNOWLEDGMENT_RESPONSES = [
    "Got it!",
    "Understood!",
    "Okay!",
    "Alright!",
    "I see!",
    "Makes sense!",
    "Noted!",
    "I understand!",
    "Roger that!",
    "Copy that!",
    "Gotcha!",
    "Clear!",
]

SORRY_RESPONSES = [
    "No need to apologize!",
    "That's okay!",
    "No worries at all!",
    "Don't worry about it!",
    "It's all good!",
    "No problem!",
    "Nothing to apologize for!",
    "All is well!",
    "It happens!",
    "Totally fine!",
]

CLARIFICATION_RESPONSES = [
    "Could you tell me more about what you mean?",
    "I'm not sure I understand. Could you rephrase that?",
    "What do you mean by that?",
    "Could you clarify what you're asking?",
    "I'd like to help, but I need more details. What exactly do you mean?",
    "Can you explain that a bit more?",
    "I'm listening - could you elaborate?",
    "Tell me more so I can help better.",
    "What are you trying to say?",
    "Help me understand - what do you need?",
]

YES_RESPONSES = [
    "Great! What else would you like to know?",
    "Okay! How can I help further?",
    "Understood! What's next?",
    "Alright! Anything else?",
    "Got it! What else can I do for you?",
    "Perfect! Is there more I can help with?",
    "Excellent! What else is on your mind?",
    "Good! Let me know if you need anything else.",
]

NO_RESPONSES = [
    "Okay, no problem!",
    "Alright, let me know if you change your mind.",
    "That's fine! What else can I help with?",
    "Okay! Is there something else I can help with?",
    "No worries! Anything else on your mind?",
    "That's okay! I'm here if you need me.",
    "Understood! Just let me know.",
    "Fair enough! What else can I do?",
]

EXCLAMATION_RESPONSES = [
    "Indeed!",
    "I agree!",
    "Absolutely!",
    "Right?",
    "I know, right?",
    "That's great!",
    "Amazing!",
    "Totally!",
    "For sure!",
    "You said it!",
]

EMOTION_HAPPY_RESPONSES = [
    "That's wonderful to hear!",
    "Great! What made you happy?",
    "I'm glad you're feeling good!",
    "That's awesome!",
    "Happiness is great! What's the occasion?",
    "Yay! I'm happy for you!",
    "That's fantastic! Tell me more!",
    "Wonderful news!",
]

EMOTION_SAD_RESPONSES = [
    "I'm sorry to hear that. Want to talk about it?",
    "That's tough. Is there anything I can help with?",
    "I understand. Sometimes talking helps.",
    "I'm here if you want to chat.",
    "That sounds difficult. What's going on?",
    "I'm sorry. Is there anything I can do?",
    "That's hard. I'm here for you.",
    "I wish I could help. Want to share?",
]

WEATHER_RESPONSES = [
    "Weather can really affect our mood! How's it where you are?",
    "Nice observation! Weather's always a good topic.",
    "I don't experience weather myself, but I understand it matters!",
    "That's interesting! How do you feel about the weather today?",
    "Weather talk! A classic. How's your day going?",
    "I can't feel the weather, but I hope it's treating you well!",
]

TEST_RESPONSES = [
    "I'm here and working! How can I help you?",
    "Test received! Everything seems to be working. What would you like to do?",
    "Hello! Yes, I'm working. What can I do for you?",
    "I'm operational! What would you like to test?",
    "All systems go! How can I help?",
    "Working perfectly! What's on your mind?",
    "Yes, I'm here! Fire away!",
]

RANDOM_INPUT_RESPONSES = [
    "I'm not sure what you mean. Could you try rephrasing that?",
    "That's interesting input! What would you like to know?",
    "I didn't quite catch that. How can I help you?",
    "Hmm, I'm not sure how to interpret that. What's on your mind?",
    "Interesting! Is there something specific I can help with?",
    "I see! What did you have in mind?",
    "Tell me more about what you need!",
]


def create_lesson(lesson_id: str, title: str, description: str, items: List[Dict],
                  category: str = "conversation", difficulty: int = 1) -> Dict[str, Any]:
    """Create a lesson structure."""
    return {
        "lesson_id": lesson_id,
        "title": title,
        "description": description,
        "category": category,
        "difficulty": difficulty,
        "estimated_minutes": max(15, len(items) // 20),
        "tags": ["dialogue", "conversation", "simple"],
        "items": items
    }


def create_item(item_id: str, source: str, target: str, context: str) -> Dict[str, Any]:
    """Create a dialogue item."""
    return {
        "id": item_id,
        "type": "dialogue",
        "source": source,
        "target": target,
        "context": context
    }


def generate_all_variations(base: str, include_typos: bool = True) -> List[str]:
    """Generate comprehensive variations of a base word."""
    variations = set()

    # Case variations
    variations.add(base.lower())
    variations.add(base.capitalize())
    variations.add(base.upper())

    # Punctuation variations
    for v in [base.lower(), base.capitalize()]:
        variations.add(f"{v}!")
        variations.add(f"{v}.")
        variations.add(f"{v}?")
        variations.add(f"{v}...")
        variations.add(f"{v}!!")
        variations.add(f"{v}!?")
        variations.add(f"{v}??")

    # With Jiyou name
    for v in [base.lower(), base.capitalize()]:
        for name in ["jiyou", "Jiyou", "JiYou"]:
            variations.add(f"{v} {name}")
            variations.add(f"{v} {name}!")
            variations.add(f"{v}, {name}")
            variations.add(f"{name} {v}")
            variations.add(f"{name}, {v}")

    # Typo variations (repeated letters)
    if include_typos and len(base) > 1:
        last = base[-1].lower()
        for i in range(1, 4):
            variations.add(base.lower() + last * i)
            variations.add(base.capitalize() + last * i)

    # With "there"
    for v in [base.lower(), base.capitalize()]:
        variations.add(f"{v} there")
        variations.add(f"{v} there!")

    return list(variations)


def generate_300_simple_greetings() -> List[Dict]:
    """Generate extensive simple greeting variations."""
    items = []
    item_num = 1
    used = set()

    # Core greetings with full variations
    core_greetings = ["hi", "hello", "hey", "heya", "hiya", "yo", "sup", "howdy", "greetings", "hola", "ello", "aloha"]

    for greeting in core_greetings:
        for var in generate_all_variations(greeting):
            if var not in used:
                used.add(var)
                items.append(create_item(f"greet_{item_num:04d}", var, random.choice(GREETING_RESPONSES), "greeting"))
                item_num += 1

    # Additional phrases
    additional = [
        # Basic greetings
        "hi hi", "hello hello", "hey hey", "hi hi hi",
        "what's good", "whats good", "wassup", "wazzup", "wazzzup",
        "good day", "g'day", "gday", "greetings and salutations",
        "bonjour", "ciao", "konnichiwa", "namaste", "salaam",

        # With context
        "hi again", "hello again", "hey again", "back again",
        "hi there", "hello there", "hey there", "hi you",
        "good to see you", "nice to see you", "nice to meet you",
        "long time no see", "it's been a while", "been a while",
        "hi friend", "hello friend", "hey friend", "hi buddy",
        "hi everyone", "hello everyone", "hey everyone", "hi all",
        "hello all", "hey all", "greetings all",

        # Time greetings
        "morning", "afternoon", "evening",
        "good morning", "good afternoon", "good evening",
        "gm", "GM", "good morn", "mornin", "mornin'",

        # Coming back
        "hi im back", "hello im back", "im back", "back",
        "hi i'm back", "i'm back", "hey i'm back",
        "hi its me", "hello its me", "its me", "it's me",
        "hey its me again", "hi its me again", "me again",

        # Casual variations
        "yoo", "yooo", "yoooo", "ayy", "ayyy", "ayyyy",
        "waddup", "what up", "whaddup", "wussup", "wsup",
        "hey yo", "yo yo", "hey hey hey",
        "hiyaa", "hellooo", "heyoo",
        "henlo", "hewwo", "hewlo",  # internet speak

        # Questions as greetings
        "anybody there", "anybody home", "anyone here",
        "is anyone there", "is anybody there",
        "are you there", "you there", "u there",
        "hello is anyone there", "hello anyone",

        # Greetings with intent
        "hi can we talk", "hello can we chat",
        "hi i have a question", "hello i need help",
        "hey quick question", "hi got a minute",
        "hello do you have time", "hey are you busy",
    ]

    for phrase in additional:
        if phrase not in used:
            used.add(phrase)
            items.append(create_item(f"greet_{item_num:04d}", phrase, random.choice(GREETING_RESPONSES), "greeting"))
            item_num += 1
            # Add with punctuation
            for p in ["!", "?", "."]:
                pv = f"{phrase}{p}"
                if pv not in used:
                    used.add(pv)
                    items.append(create_item(f"greet_{item_num:04d}", pv, random.choice(GREETING_RESPONSES), "greeting"))
                    item_num += 1

    return items


def generate_301_simple_farewells() -> List[Dict]:
    """Generate extensive farewell variations."""
    items = []
    item_num = 1
    used = set()

    core_farewells = ["bye", "goodbye", "cya", "later", "peace", "adios", "ciao", "cheerio", "farewell", "byebye"]

    for farewell in core_farewells:
        for var in generate_all_variations(farewell, include_typos=False):
            if var not in used:
                used.add(var)
                items.append(create_item(f"farewell_{item_num:04d}", var, random.choice(FAREWELL_RESPONSES), "farewell"))
                item_num += 1

    additional = [
        # Basic farewells
        "bye bye", "byebye", "buh bye", "bai", "baii", "baiii",
        "see ya", "see you", "see you later", "see ya later",
        "catch you later", "catch ya later", "catcha later",
        "talk to you later", "talk later", "ttyl", "TTYL",
        "gotta go", "i gotta go", "got to go", "gtg", "GTG",
        "heading out", "im heading out", "i'm heading out",
        "im leaving", "im going", "i have to go", "i must go",
        "take care", "be well", "stay safe", "stay well",
        "good night", "goodnight", "night night", "nighty night",
        "sweet dreams", "sleep well", "sleep tight",
        "bye jiyou", "goodbye jiyou", "later jiyou", "see ya jiyou",
        "bye for now", "goodbye for now", "for now",
        "until next time", "till next time", "til next time",
        "so long", "im off", "im out", "i'm off", "i'm out",
        "peace out", "deuces", "laters", "laterz",
        "have a good one", "have a nice day", "have a good day",
        "have a great day", "enjoy your day",
        "take it easy", "be good", "be safe",
        "gn", "GN", "nite", "nitey nite",
        "signing off", "logging off", "gotta run",
        "brb", "BRB", "be right back", "back soon",
        "afk", "AFK", "going afk",
        "time to go", "its time to go", "i should go",
        "ok bye", "okay bye", "alright bye", "k bye",
        "well bye", "so bye", "anyway bye",
        "thats all", "that's all", "thats it", "that's it",
        "done", "im done", "all done", "finished",
        "end", "the end", "over and out",
    ]

    for phrase in additional:
        if phrase not in used:
            used.add(phrase)
            items.append(create_item(f"farewell_{item_num:04d}", phrase, random.choice(FAREWELL_RESPONSES), "farewell"))
            item_num += 1
            for p in ["!", "."]:
                pv = f"{phrase}{p}"
                if pv not in used:
                    used.add(pv)
                    items.append(create_item(f"farewell_{item_num:04d}", pv, random.choice(FAREWELL_RESPONSES), "farewell"))
                    item_num += 1

    return items


def generate_302_simple_questions() -> List[Dict]:
    """Generate extensive 'what's up' and 'how are you' variations."""
    items = []
    item_num = 1
    used = set()

    # What's up variations
    whats_up = [
        "what's up", "whats up", "wassup", "wazzup", "sup", "wut up",
        "what up", "whatup", "watsup", "wussup", "wsup",
        "what is up", "what's going on", "whats going on",
        "what's happening", "whats happening", "what is happening",
        "what's new", "whats new", "what is new", "anything new",
        "what's the word", "whats the word",
        "what's cooking", "whats cooking",
        "what's shaking", "whats shaking",
        "what's popping", "whats popping",
        "what's good", "whats good", "what good",
        "what's the news", "any news", "news",
        "what's crackin", "whats crackin", "what's cracking",
    ]

    for q in whats_up:
        for var in [q, q.capitalize(), f"{q}?", f"{q.capitalize()}?"]:
            if var not in used:
                used.add(var)
                items.append(create_item(f"q_{item_num:04d}", var, random.choice(WHATS_UP_RESPONSES), "whats_up"))
                item_num += 1
        # With Jiyou
        for name in ["jiyou", "Jiyou"]:
            v = f"{q} {name}"
            if v not in used:
                used.add(v)
                items.append(create_item(f"q_{item_num:04d}", v, random.choice(WHATS_UP_RESPONSES), "whats_up"))
                item_num += 1

    # How are you variations
    how_are_you = [
        "how are you", "how r u", "how are u", "how r you",
        "how are you doing", "how you doing", "how u doing",
        "how's it going", "hows it going", "how is it going",
        "how are things", "how's things", "hows things",
        "how's life", "hows life", "how is life",
        "how've you been", "how have you been", "how you been",
        "how ya doing", "how ya doin", "howdy doing",
        "you good", "u good", "you okay", "u okay", "u ok",
        "you alright", "u alright", "you aight", "u aight",
        "everything okay", "everything ok", "everything good",
        "all good", "all well", "doing well", "doing good",
        "how do you do", "how goes it", "how goes",
        "how's your day", "hows your day", "how is your day",
        "how's it been", "hows it been",
        "you doing okay", "you doing alright", "you holding up",
        "how are we doing", "how we doing",
        "whats going on with you", "what's going on with you",
        "how is everything", "hows everything",
    ]

    for q in how_are_you:
        for var in [q, q.capitalize(), f"{q}?", f"{q.capitalize()}?"]:
            if var not in used:
                used.add(var)
                items.append(create_item(f"q_{item_num:04d}", var, random.choice(HOW_ARE_YOU_RESPONSES), "how_are_you"))
                item_num += 1
        for name in ["jiyou", "Jiyou"]:
            v = f"{q} {name}"
            if v not in used:
                used.add(v)
                items.append(create_item(f"q_{item_num:04d}", v, random.choice(HOW_ARE_YOU_RESPONSES), "how_are_you"))
                item_num += 1

    return items


def generate_303_identity_questions() -> List[Dict]:
    """Generate extensive identity questions."""
    items = []
    item_num = 1
    used = set()

    who_questions = [
        "who are you", "who r u", "who r you", "who are u",
        "who is this", "whos this", "who's this", "who dis",
        "who am i talking to", "who am i speaking to",
        "who is jiyou", "who is Jiyou", "who is JiYou",
        "whats your name", "what's your name", "what is your name",
        "your name", "name", "tell me your name",
        "introduce yourself", "tell me about yourself",
        "are you jiyou", "are you Jiyou", "r u jiyou",
        "is this jiyou", "is this Jiyou",
        "what should i call you", "what can i call you",
        "who made you", "who created you", "who built you",
        "what are you called", "how should i address you",
    ]

    for q in who_questions:
        for var in [q, q.capitalize(), f"{q}?", f"{q.capitalize()}?"]:
            if var not in used:
                used.add(var)
                items.append(create_item(f"id_{item_num:04d}", var, random.choice(IDENTITY_RESPONSES), "identity"))
                item_num += 1

    what_questions = [
        "what are you", "what r u", "what are u",
        "what is this", "whats this", "what's this",
        "what am i talking to", "what am i speaking with",
        "are you a bot", "are you a chatbot", "r u a bot",
        "are you ai", "are you an ai", "are you an AI", "r u ai",
        "are you a robot", "r u a robot", "you a robot",
        "are you human", "are you a human", "r u human",
        "are you real", "r u real", "you real",
        "are you a person", "are you a computer", "are you a machine",
        "are you alive", "r u alive", "you alive",
        "are you sentient", "are you conscious", "are you aware",
        "what kind of ai are you", "what kind of AI are you",
        "what type of ai", "what type of AI",
        "how do you work", "how does this work",
        "what makes you different", "how are you different",
        "are you like chatgpt", "are you like ChatGPT",
        "how are you different from chatgpt",
        "what is a spiking neural network",
        "do you have feelings", "can you feel",
        "do you think", "can you think",
        "are you smart", "are you intelligent",
    ]

    for q in what_questions:
        for var in [q, q.capitalize(), f"{q}?", f"{q.capitalize()}?"]:
            if var not in used:
                used.add(var)
                items.append(create_item(f"id_{item_num:04d}", var, random.choice(IDENTITY_RESPONSES), "identity"))
                item_num += 1

    capability_questions = [
        "what can you do", "what do you do", "what can u do",
        "what are you capable of", "what are your capabilities",
        "what can you help with", "what are you good at",
        "tell me what you can do", "show me what you can do",
        "can you help me", "can you help", "can u help",
        "how can you help", "how can you help me",
        "what do you know", "what can you know",
        "what can i ask you", "what should i ask you",
        "help me understand you", "explain yourself",
        "what tools do you have", "do you have tools",
        "can you search the web", "can you google",
        "can you do math", "can you calculate", "can you compute",
        "can you remember things", "can you learn",
        "what are your functions", "what functions do you have",
        "what are you for", "what is your purpose",
        "why do you exist", "what were you made for",
    ]

    for q in capability_questions:
        for var in [q, q.capitalize(), f"{q}?", f"{q.capitalize()}?"]:
            if var not in used:
                used.add(var)
                items.append(create_item(f"id_{item_num:04d}", var, random.choice(CAPABILITY_RESPONSES), "capabilities"))
                item_num += 1

    return items


def generate_304_help_requests() -> List[Dict]:
    """Generate extensive help request variations."""
    items = []
    item_num = 1
    used = set()

    help_phrases = [
        # Basic
        "help", "Help", "HELP", "help!", "help?", "help me",
        "help me please", "please help", "please help me",
        "i need help", "I need help", "need help",
        "can you help", "can you help me", "can u help",
        "could you help", "could you help me", "would you help",
        "will you help", "will you help me",
        "i need assistance", "need assistance", "assistance",
        "can you assist", "can you assist me", "assist me",
        "i have a question", "I have a question", "got a question",
        "quick question", "question for you", "question",
        "can i ask something", "can i ask you something",
        "may i ask", "may i ask something", "let me ask",
        "i need your help", "need your help",
        "i need some help", "need some help", "some help",
        "help me out", "help me out please", "lend me a hand",
        "give me a hand", "i could use some help",
        "im stuck", "i'm stuck", "stuck", "im lost", "i'm lost",
        "i dont know what to do", "i don't know what to do",
        "im confused", "i'm confused", "confused",
        "i need advice", "need advice", "advice",
        "what should i do", "what do i do", "what to do",
        "can you help with something", "help with something",
        "i need to ask", "need to ask you", "asking for help",
        "requesting help", "request help", "sos", "SOS",
        "mayday", "emergency", "urgent", "urgent help",
    ]

    for phrase in help_phrases:
        if phrase not in used:
            used.add(phrase)
            items.append(create_item(f"help_{item_num:04d}", phrase, random.choice(HELP_RESPONSES), "help"))
            item_num += 1
        # With jiyou
        for name in ["jiyou", "Jiyou"]:
            v = f"{phrase} {name}"
            if v not in used:
                used.add(v)
                items.append(create_item(f"help_{item_num:04d}", v, random.choice(HELP_RESPONSES), "help"))
                item_num += 1

    return items


def generate_305_acknowledgments() -> List[Dict]:
    """Generate extensive acknowledgment variations."""
    items = []
    item_num = 1
    used = set()

    ok_phrases = [
        "ok", "okay", "Ok", "OK", "Okay", "OKAY", "k", "K",
        "ok!", "okay!", "ok.", "okay.", "okey", "okee",
        "kk", "kk!", "okey dokey", "okie dokie", "okie",
        "alright", "alright!", "all right", "aight", "ight",
        "right", "right!", "right.", "rite",
        "sure", "sure!", "sure.", "Sure", "SURE",
        "yep", "yup", "yeah", "yea", "ya", "ye",
        "yes", "Yes", "YES", "yes!", "yess", "yesss",
        "mhm", "mmhm", "uh huh", "uhuh", "mhmm",
        "gotcha", "got it", "got it!", "I got it", "i got it",
        "understood", "i understand", "I understand",
        "makes sense", "that makes sense", "ok makes sense",
        "i see", "I see", "ah i see", "oh i see",
        "oh okay", "oh ok", "ah okay", "ah ok",
        "fair enough", "fair", "noted", "noted!",
        "copy that", "roger", "roger that", "copy",
        "affirmative", "aye", "aye aye",
        "sounds good", "sounds great", "sounds fine", "sounds right",
        "perfect", "great", "good", "fine", "nice",
        "cool", "cool!", "Cool", "COOL", "kool",
        "nice", "nice!", "Nice", "noice",
        "awesome", "awesome!", "Awesome", "AWESOME",
        "sweet", "sweet!", "dope", "bet", "Bet", "BET",
        "word", "Word", "facts", "true", "tru",
        "valid", "legit", "solid",
    ]

    for phrase in ok_phrases:
        if phrase not in used:
            used.add(phrase)
            items.append(create_item(f"ack_{item_num:04d}", phrase, random.choice(ACKNOWLEDGMENT_RESPONSES), "ack"))
            item_num += 1

    return items


def generate_306_emotional_responses() -> List[Dict]:
    """Generate emotional state variations."""
    items = []
    item_num = 1
    used = set()

    happy_phrases = [
        "im happy", "i'm happy", "I'm happy", "im so happy",
        "feeling happy", "feeling good", "feeling great",
        "im excited", "i'm excited", "so excited", "excited",
        "im glad", "i'm glad", "glad", "very glad",
        "im pleased", "i'm pleased", "pleased",
        "im thrilled", "i'm thrilled", "thrilled",
        "im joyful", "i'm joyful", "joyful",
        "i feel good", "i feel great", "i feel amazing",
        "i feel wonderful", "i feel fantastic", "i feel awesome",
        "today is a good day", "good day today", "great day",
        "great news", "i have great news", "good news",
        "something good happened", "good things happened",
        "im in a good mood", "i'm in a good mood", "good mood",
        "so happy", "very happy", "really happy",
        "im overjoyed", "ecstatic", "elated",
        "yay", "yay!", "YAY", "woohoo", "woo", "woot",
        "yayyy", "yayy", "wooo", "woooo",
    ]

    for phrase in happy_phrases:
        if phrase not in used:
            used.add(phrase)
            items.append(create_item(f"emotion_{item_num:04d}", phrase, random.choice(EMOTION_HAPPY_RESPONSES), "happy"))
            item_num += 1

    sad_phrases = [
        "im sad", "i'm sad", "I'm sad", "im so sad", "sad",
        "feeling sad", "feeling down", "feeling low", "feeling blue",
        "im unhappy", "i'm unhappy", "unhappy",
        "im depressed", "i'm depressed", "feeling depressed", "depressed",
        "im upset", "i'm upset", "feeling upset", "upset",
        "im disappointed", "i'm disappointed", "disappointed",
        "im frustrated", "i'm frustrated", "frustrated",
        "im stressed", "i'm stressed", "stressed", "stressed out",
        "im anxious", "i'm anxious", "anxious", "anxiety",
        "im worried", "i'm worried", "worried", "worrying",
        "i feel bad", "i feel awful", "i feel terrible",
        "i feel down", "i feel low", "i feel horrible",
        "today is a bad day", "bad day today", "terrible day",
        "something bad happened", "bad things happened",
        "im having a rough day", "i'm having a rough day",
        "im not doing well", "i'm not doing well", "not well",
        "not great", "not good", "not okay", "not ok",
        "im hurt", "i'm hurt", "hurt", "hurting",
        "im lonely", "i'm lonely", "lonely", "alone",
        "im scared", "i'm scared", "scared", "afraid", "fearful",
        "im angry", "i'm angry", "angry", "mad", "furious",
        "im annoyed", "i'm annoyed", "annoyed", "irritated",
    ]

    for phrase in sad_phrases:
        if phrase not in used:
            used.add(phrase)
            items.append(create_item(f"emotion_{item_num:04d}", phrase, random.choice(EMOTION_SAD_RESPONSES), "sad"))
            item_num += 1

    tired_phrases = [
        "im tired", "i'm tired", "tired", "so tired", "very tired",
        "exhausted", "im exhausted", "i'm exhausted",
        "sleepy", "im sleepy", "i'm sleepy", "so sleepy",
        "need sleep", "i need sleep", "need rest", "need to rest",
        "cant sleep", "can't sleep", "i cant sleep", "cannot sleep",
        "im drained", "i'm drained", "drained", "feeling drained",
        "burned out", "burnt out", "im burned out", "burnout",
        "low energy", "no energy", "i have no energy",
        "fatigued", "wiped out", "beat", "zonked",
        "running on empty", "dead tired", "dog tired",
    ]

    tired_responses = [
        "Rest is important! Have you been getting enough sleep?",
        "That sounds exhausting. Make sure to take care of yourself!",
        "Being tired is tough. Is there anything I can help with to lighten your load?",
        "Sounds like you need some rest. Take it easy!",
        "I hope you can get some rest soon!",
    ]

    for phrase in tired_phrases:
        if phrase not in used:
            used.add(phrase)
            items.append(create_item(f"emotion_{item_num:04d}", phrase, random.choice(tired_responses), "tired"))
            item_num += 1

    return items


def generate_307_small_talk_weather() -> List[Dict]:
    """Generate weather small talk."""
    items = []
    item_num = 1
    used = set()

    weather_phrases = [
        "nice weather", "nice weather today", "the weather is nice",
        "beautiful day", "what a beautiful day", "lovely day",
        "gorgeous day", "perfect weather", "great weather",
        "its hot", "it's hot", "so hot", "too hot", "hot today",
        "its cold", "it's cold", "so cold", "too cold", "cold today",
        "its warm", "it's warm", "warm today", "nice and warm",
        "its cool", "it's cool", "cool out", "cool today",
        "its raining", "it's raining", "raining", "rain",
        "its snowing", "it's snowing", "snowing", "snow",
        "its sunny", "it's sunny", "sunny", "sun is out",
        "its cloudy", "it's cloudy", "cloudy", "overcast",
        "its windy", "it's windy", "windy", "wind",
        "its humid", "it's humid", "humid", "muggy",
        "bad weather", "terrible weather", "awful weather",
        "weather sucks", "hate this weather", "hate the weather",
        "love this weather", "perfect weather", "ideal weather",
        "how's the weather", "hows the weather", "weather report",
        "whats the weather like", "what's the weather like",
        "nice day out", "nice day outside", "nice out",
        "horrible day", "terrible day", "gross out",
        "storm coming", "looks like rain", "looks like snow",
        "freezing", "its freezing", "so cold", "freezing cold",
        "boiling", "its boiling", "scorching", "burning up",
    ]

    for phrase in weather_phrases:
        if phrase not in used:
            used.add(phrase)
            items.append(create_item(f"weather_{item_num:04d}", phrase, random.choice(WEATHER_RESPONSES), "weather"))
            item_num += 1

    return items


def generate_308_small_talk_time() -> List[Dict]:
    """Generate time-related greetings."""
    items = []
    item_num = 1
    used = set()

    time_greetings = [
        "good morning", "Good morning", "GOOD MORNING", "good morning!",
        "morning", "Morning", "mornin", "mornin!", "mornin'",
        "gm", "GM", "g morning", "gud morning",
        "good afternoon", "Good afternoon", "afternoon",
        "good evening", "Good evening", "evening", "evenin",
        "good night", "Good night", "goodnight", "Goodnight",
        "night", "nite", "g'night", "gnight", "gn", "GN",
        "nitey nite", "night night", "nighty night",
        "its late", "it's late", "getting late", "late night",
        "its early", "it's early", "so early", "early morning",
        "cant sleep", "can't sleep", "i cant sleep", "insomnia",
        "up late", "im up late", "i'm up late", "staying up late",
        "up early", "im up early", "i'm up early", "woke up early",
        "long day", "its been a long day", "what a day", "long day today",
        "long night", "its been a long night", "what a night",
        "busy day", "its been busy", "been busy", "busy busy",
    ]

    time_responses = [
        "Hello! I hope your day/night is going well!",
        "Hi there! Time flies, doesn't it?",
        "Hey! Whatever time it is, I'm here to help!",
        "Hello! How's your day been so far?",
        "Hi! I hope you're doing well!",
        "Good to hear from you! How's it going?",
        "Hey! Ready to help whenever you need!",
    ]

    for phrase in time_greetings:
        if phrase not in used:
            used.add(phrase)
            items.append(create_item(f"time_{item_num:04d}", phrase, random.choice(time_responses), "time"))
            item_num += 1
        # With jiyou
        for name in ["jiyou", "Jiyou"]:
            v = f"{phrase} {name}"
            if v not in used:
                used.add(v)
                items.append(create_item(f"time_{item_num:04d}", v, random.choice(time_responses), "time"))
                item_num += 1

    return items


def generate_309_capability_questions() -> List[Dict]:
    """Generate 'can you X' style questions."""
    items = []
    item_num = 1
    used = set()

    abilities = [
        "think", "learn", "remember", "forget", "understand", "comprehend",
        "read", "write", "speak", "listen", "hear", "see",
        "calculate", "compute", "do math", "solve math", "add", "subtract", "multiply", "divide",
        "search", "look up", "find", "google", "research",
        "help", "assist", "support", "guide",
        "chat", "talk", "converse", "have a conversation", "discuss",
        "answer questions", "answer", "respond", "reply",
        "give advice", "advise", "recommend", "suggest",
        "explain", "clarify", "describe", "define",
        "summarize", "translate", "paraphrase",
        "tell jokes", "be funny", "make jokes", "tell a joke",
        "tell stories", "tell a story", "make up a story",
        "code", "program", "write code", "debug",
        "sing", "draw", "create", "make", "build",
    ]

    prefixes = [
        "can you", "could you", "are you able to", "do you know how to",
        "do you", "can u", "could u", "r u able to", "will you",
        "would you", "are you capable of",
    ]

    capability_responses = CAPABILITY_RESPONSES + [
        "I can certainly try! What specifically do you need?",
        "That's something I can help with! Tell me more.",
        "Yes, I should be able to help with that!",
        "I'll do my best! What do you need?",
        "Let's give it a try! What's the task?",
    ]

    for prefix in prefixes:
        for ability in abilities:
            q = f"{prefix} {ability}"
            if q not in used:
                used.add(q)
                items.append(create_item(f"cap_{item_num:04d}", q, random.choice(capability_responses), "capability"))
                item_num += 1
            qm = f"{q}?"
            if qm not in used:
                used.add(qm)
                items.append(create_item(f"cap_{item_num:04d}", qm, random.choice(capability_responses), "capability"))
                item_num += 1

    return items


def generate_310_opinion_requests() -> List[Dict]:
    """Generate opinion request variations."""
    items = []
    item_num = 1
    used = set()

    opinion_phrases = [
        "what do you think", "what do u think", "what you think",
        "whats your opinion", "what's your opinion", "your opinion",
        "your thoughts", "ur thoughts", "thoughts",
        "how do you feel about", "how do you feel", "how u feel",
        "do you think", "do you believe", "do u think",
        "what would you say", "what would you do", "what would u do",
        "in your opinion", "your opinion on", "opinion on",
        "thoughts on", "what say you", "any thoughts",
        "agree or disagree", "do you agree", "do u agree",
        "is that right", "am i right", "right",
        "what do u think", "wdyt", "WDYT",
        "your take", "your view", "your perspective",
        "how do you see it", "whats your take",
        "your two cents", "your input",
    ]

    opinion_responses = [
        "That's an interesting question! Let me think about it...",
        "I appreciate you asking for my perspective!",
        "Hmm, that's worth considering from multiple angles.",
        "Good question! What's the context?",
        "I'd need to know more to give a thoughtful answer. What specifically are you asking about?",
        "Interesting! What made you think of that?",
        "Let me share my thoughts on that...",
    ]

    for phrase in opinion_phrases:
        if phrase not in used:
            used.add(phrase)
            items.append(create_item(f"opinion_{item_num:04d}", phrase, random.choice(opinion_responses), "opinion"))
            item_num += 1
        qm = f"{phrase}?"
        if qm not in used:
            used.add(qm)
            items.append(create_item(f"opinion_{item_num:04d}", qm, random.choice(opinion_responses), "opinion"))
            item_num += 1

    return items


def generate_311_clarification() -> List[Dict]:
    """Generate clarification request variations."""
    items = []
    item_num = 1
    used = set()

    clarification_phrases = [
        "what", "What", "WHAT", "what?", "What?",
        "huh", "Huh", "huh?", "Huh?",
        "hmm", "Hmm", "hm", "hmm?",
        "sorry", "sorry?", "pardon", "pardon?", "pardon me",
        "come again", "come again?", "say again",
        "say that again", "say what", "say what?",
        "repeat that", "can you repeat", "repeat please",
        "i dont understand", "i don't understand", "dont understand",
        "confused", "im confused", "i'm confused",
        "lost", "im lost", "i'm lost", "you lost me",
        "what do you mean", "what does that mean", "what that mean",
        "meaning", "meaning?", "what meaning",
        "explain", "explain?", "please explain", "explain that",
        "clarify", "please clarify", "can you clarify",
        "elaborate", "can you elaborate", "elaborate please",
        "more details", "more info", "more information",
        "not sure i follow", "dont follow", "not following",
        "???", "??", "?", "?????",
        "idk", "i dont know", "i don't know", "dunno",
        "hm", "um", "uh", "er",
        "wut", "wat", "wha", "eh",
        "could you explain", "explain more", "tell me more",
        "what now", "now what", "and then",
        "so", "so?", "so what", "meaning what",
    ]

    for phrase in clarification_phrases:
        if phrase not in used:
            used.add(phrase)
            items.append(create_item(f"clarify_{item_num:04d}", phrase, random.choice(CLARIFICATION_RESPONSES), "clarify"))
            item_num += 1

    return items


def generate_312_affirmations() -> List[Dict]:
    """Generate yes/no/maybe variations."""
    items = []
    item_num = 1
    used = set()

    yes_phrases = [
        "yes", "Yes", "YES", "yes!", "yess", "yesss",
        "yeah", "yea", "yep", "yup", "ya", "ye", "yah",
        "sure", "Sure", "sure!", "SURE",
        "definitely", "absolutely", "certainly", "positively",
        "of course", "for sure", "totally", "completely",
        "correct", "thats right", "that's right", "right",
        "exactly", "precisely", "indeed", "true",
        "thats true", "that's true", "so true", "very true",
        "i agree", "agreed", "i concur", "concur",
        "yessir", "yes sir", "yes ma'am", "yes maam",
        "uh huh", "mhm", "mmhm", "yuh", "yuh huh",
        "affirmative", "positive", "confirmed", "confirm",
        "100%", "100 percent", "absolutely yes",
        "obviously", "clearly", "naturally",
        "you bet", "you betcha", "damn right", "hell yes",
        "for real", "fr", "no doubt", "no cap",
    ]

    for phrase in yes_phrases:
        if phrase not in used:
            used.add(phrase)
            items.append(create_item(f"affirm_{item_num:04d}", phrase, random.choice(YES_RESPONSES), "yes"))
            item_num += 1

    no_phrases = [
        "no", "No", "NO", "no!", "noo", "nooo",
        "nope", "nah", "nay", "na", "nuh uh",
        "no way", "no thanks", "no thank you", "no thx",
        "not really", "not quite", "not exactly",
        "negative", "false", "incorrect",
        "i disagree", "disagree", "i dont agree",
        "wrong", "thats wrong", "that's wrong",
        "incorrect", "thats incorrect", "that's incorrect",
        "i dont think so", "i don't think so", "dont think so",
        "dont believe so", "don't believe so",
        "probably not", "definitely not", "certainly not",
        "absolutely not", "never", "no way jose",
        "not at all", "nah fam", "hell no",
        "hard no", "big no", "thats a no",
    ]

    for phrase in no_phrases:
        if phrase not in used:
            used.add(phrase)
            items.append(create_item(f"affirm_{item_num:04d}", phrase, random.choice(NO_RESPONSES), "no"))
            item_num += 1

    maybe_phrases = [
        "maybe", "Maybe", "MAYBE", "perhaps", "possibly",
        "probably", "likely", "unlikely",
        "i guess", "i suppose", "suppose so",
        "kind of", "kinda", "sort of", "sorta",
        "not sure", "im not sure", "i'm not sure",
        "dont know", "dunno", "idk", "IDK",
        "could be", "might be", "may be",
        "depends", "it depends", "that depends",
        "sometimes", "occasionally", "on occasion",
        "50/50", "fifty fifty", "half and half",
        "eh", "meh", "i mean", "i dunno",
    ]

    maybe_responses = [
        "I understand the uncertainty. Would you like to talk more about it?",
        "That's fair. Let me know if I can help clarify anything.",
        "Sometimes things aren't black and white. What's making you uncertain?",
        "I get it. Is there anything specific I can help with?",
    ]

    for phrase in maybe_phrases:
        if phrase not in used:
            used.add(phrase)
            items.append(create_item(f"affirm_{item_num:04d}", phrase, random.choice(maybe_responses), "maybe"))
            item_num += 1

    return items


def generate_313_casual_fillers() -> List[Dict]:
    """Generate casual filler variations."""
    items = []
    item_num = 1
    used = set()

    filler_phrases = [
        "um", "umm", "ummm", "ummmm",
        "uh", "uhh", "uhhh", "uhhhh",
        "er", "err", "errr", "erm",
        "hmm", "hmmm", "hmmmm", "hm",
        "well", "well...", "well,", "well then",
        "so", "so...", "so,", "soo",
        "anyway", "anyways", "anyhow", "anyway...",
        "like", "like...", "like,",
        "you know", "ya know", "yknow", "y'know",
        "i mean", "i mean...", "imean",
        "basically", "essentially", "fundamentally",
        "honestly", "to be honest", "tbh", "TBH",
        "actually", "in fact", "actually...",
        "right so", "ok so", "okay so", "so like",
        "let me think", "let me see", "lemme think",
        "hold on", "wait", "wait a sec", "wait a minute",
        "one moment", "just a moment", "one sec",
        "hang on", "sec", "one sec", "gimme a sec",
        "brb", "BRB", "be right back",
    ]

    filler_responses = [
        "Take your time! I'm listening.",
        "I'm here when you're ready.",
        "No rush! What's on your mind?",
        "Go ahead, I'm listening.",
        "I'm patient! What would you like to say?",
        "Ready when you are!",
    ]

    for phrase in filler_phrases:
        if phrase not in used:
            used.add(phrase)
            items.append(create_item(f"filler_{item_num:04d}", phrase, random.choice(filler_responses), "filler"))
            item_num += 1

    return items


def generate_314_exclamations() -> List[Dict]:
    """Generate exclamation variations."""
    items = []
    item_num = 1
    used = set()

    positive = [
        "wow", "Wow", "WOW", "wow!", "woww", "wowww",
        "amazing", "Amazing", "amazing!", "AMAZING",
        "awesome", "Awesome", "awesome!", "AWESOME",
        "cool", "Cool", "cool!", "COOL", "coool",
        "nice", "Nice", "nice!", "NICE", "niice",
        "great", "Great", "great!", "GREAT",
        "fantastic", "wonderful", "incredible", "unbelievable",
        "brilliant", "excellent", "perfect", "superb",
        "sweet", "Sweet", "sweet!", "SWEET",
        "dope", "sick", "rad", "gnarly",
        "fire", "lit", "based", "goated",
        "omg", "OMG", "oh my god", "oh my gosh",
        "oh wow", "oh nice", "oh cool", "oh great",
        "thats amazing", "thats awesome", "thats incredible",
        "thats cool", "thats great", "thats perfect",
        "no way", "for real", "seriously", "really",
        "impressive", "insane", "crazy", "wild",
        "whoa", "woah", "wooow", "sheesh",
        "dayum", "damn", "dang", "dayumn",
        "legendary", "epic", "clutch", "pog", "poggers",
    ]

    for phrase in positive:
        if phrase not in used:
            used.add(phrase)
            items.append(create_item(f"exclaim_{item_num:04d}", phrase, random.choice(EXCLAMATION_RESPONSES), "positive"))
            item_num += 1

    negative = [
        "oh no", "Oh no", "oh no!", "OH NO",
        "ugh", "Ugh", "ughhh", "UGHH",
        "damn", "dang", "darn", "dangit",
        "crap", "shoot", "rats", "crud",
        "yikes", "yikes!", "YIKES", "yikess",
        "oof", "ouch", "OOF", "big oof",
        "that sucks", "that's bad", "thats bad",
        "terrible", "awful", "horrible", "dreadful",
        "disappointing", "frustrating", "annoying",
        "oh man", "oh boy", "oh dear", "oh god",
        "geez", "jeez", "sheesh", "gosh",
        "bruh", "bro", "dude", "man",
        "smh", "SMH", "fml", "FML",
        "rip", "RIP", "welp", "gg",
    ]

    negative_responses = [
        "That sounds frustrating. What's going on?",
        "I'm sorry to hear that. Want to talk about it?",
        "That doesn't sound good. Is there anything I can help with?",
        "I understand the frustration. What happened?",
        "That's rough. I'm here if you want to share.",
    ]

    for phrase in negative:
        if phrase not in used:
            used.add(phrase)
            items.append(create_item(f"exclaim_{item_num:04d}", phrase, random.choice(negative_responses), "negative"))
            item_num += 1

    return items


def generate_315_negative_responses() -> List[Dict]:
    """Generate negative/decline variations."""
    items = []
    item_num = 1
    used = set()

    decline_phrases = [
        "no thanks", "no thank you", "No thanks", "nah thanks",
        "no need", "not needed", "dont need", "don't need",
        "im good", "i'm good", "im fine", "i'm fine", "im ok",
        "all good", "all set", "im all set", "i'm all set",
        "pass", "ill pass", "i'll pass", "i pass",
        "not interested", "not for me", "no interest",
        "maybe later", "perhaps later", "some other time",
        "not now", "not right now", "not today", "not tonight",
        "skip", "lets skip", "skip that", "skip it",
        "never mind", "nevermind", "nvm", "NVM",
        "forget it", "forget that", "forget about it",
        "dont bother", "dont worry about it", "don't worry",
        "its fine", "it's fine", "its ok", "its okay",
        "leave it", "drop it", "let it go",
        "not necessary", "unnecessary", "no need for that",
        "im okay", "i'm okay", "im alright", "i'm alright",
        "dont want it", "don't want", "no want",
        "hard pass", "thats a pass", "gonna pass",
    ]

    decline_responses = [
        "Okay, no problem! Let me know if you change your mind.",
        "That's fine! Is there something else I can help with?",
        "Understood! I'm here if you need anything.",
        "Alright! Just say the word if you need help later.",
        "No worries! I'm here when you need me.",
    ]

    for phrase in decline_phrases:
        if phrase not in used:
            used.add(phrase)
            items.append(create_item(f"decline_{item_num:04d}", phrase, random.choice(decline_responses), "decline"))
            item_num += 1

    return items


def generate_316_courtesy() -> List[Dict]:
    """Generate courtesy phrase variations."""
    items = []
    item_num = 1
    used = set()

    thanks = [
        "thanks", "Thanks", "THANKS", "thanks!",
        "thank you", "Thank you", "thank you!", "THANK YOU",
        "ty", "TY", "thx", "THX", "thnx", "thnks",
        "thanks a lot", "thanks a bunch", "thanks a ton",
        "thank you so much", "thanks so much", "tysm", "TYSM",
        "many thanks", "much appreciated", "appreciate it",
        "i appreciate it", "I appreciate it", "appreciated",
        "thank you very much", "thanks very much",
        "thanks for that", "thanks for your help",
        "thanks jiyou", "thank you jiyou", "ty jiyou",
        "grateful", "im grateful", "so grateful",
        "thats helpful", "that's helpful", "very helpful",
        "that was helpful", "so helpful", "super helpful",
        "thanks for helping", "thanks for the help",
        "cheers", "Cheers", "cheers mate",
        "bless", "bless you", "god bless",
        "ta", "Ta", "ta very much",
    ]

    for phrase in thanks:
        if phrase not in used:
            used.add(phrase)
            items.append(create_item(f"courtesy_{item_num:04d}", phrase, random.choice(THANKS_RESPONSES), "thanks"))
            item_num += 1

    please_phrases = [
        "please", "Please", "PLEASE", "please!",
        "pls", "plz", "plse", "PLS", "PLZ",
        "pretty please", "pretty plz", "pretty pls",
        "please help", "help please", "pls help",
        "if you could", "if you would", "if possible",
        "would you please", "could you please",
        "i would appreciate", "would appreciate",
        "kindly", "if you dont mind", "if you don't mind",
    ]

    please_responses = [
        "Of course! What do you need?",
        "I'd be happy to help! What can I do?",
        "Sure thing! Tell me more.",
        "Absolutely! How can I assist?",
        "Certainly! What would you like?",
    ]

    for phrase in please_phrases:
        if phrase not in used:
            used.add(phrase)
            items.append(create_item(f"courtesy_{item_num:04d}", phrase, random.choice(please_responses), "please"))
            item_num += 1

    sorry_phrases = [
        "sorry", "Sorry", "SORRY", "sorry!",
        "im sorry", "i'm sorry", "so sorry", "very sorry",
        "my bad", "my mistake", "my fault", "my apologies",
        "apologies", "i apologize", "sincere apologies",
        "pardon me", "excuse me", "pardon",
        "forgive me", "please forgive", "forgive me please",
        "oops", "whoops", "oopsie", "whoopsie",
        "sorry about that", "sorry for that", "sorry bout that",
        "didnt mean to", "didn't mean to", "didn't mean it",
        "my mistake", "i messed up", "i screwed up",
    ]

    for phrase in sorry_phrases:
        if phrase not in used:
            used.add(phrase)
            items.append(create_item(f"courtesy_{item_num:04d}", phrase, random.choice(SORRY_RESPONSES), "sorry"))
            item_num += 1

    return items


def generate_317_name_variations() -> List[Dict]:
    """Generate Jiyou name variations."""
    items = []
    item_num = 1
    used = set()

    name_phrases = [
        "jiyou", "Jiyou", "JIYOU", "JiYou", "Ji You",
        "ji you", "Ji you", "jiYou",
        "jiyou!", "Jiyou!", "jiyou?", "Jiyou?",
        "hey jiyou", "Hey Jiyou", "hey JiYou",
        "hi jiyou", "Hi Jiyou", "hi JiYou",
        "hello jiyou", "Hello Jiyou", "hello JiYou",
        "yo jiyou", "sup jiyou", "sup Jiyou",
        "dear jiyou", "hey there jiyou", "hi there jiyou",
        "jiyou help", "jiyou help me", "Jiyou help",
        "jiyou please", "please jiyou", "Jiyou please",
        "thanks jiyou", "thank you jiyou", "ty jiyou",
        "jiyou can you", "jiyou do you", "Jiyou can you",
        "excuse me jiyou", "jiyou excuse me",
        "listen jiyou", "jiyou listen", "Jiyou listen",
        "ok jiyou", "okay jiyou", "alright jiyou",
        "good job jiyou", "well done jiyou", "nice jiyou",
        "love you jiyou", "i like you jiyou", "love ya jiyou",
        "jiyou are you there", "jiyou you there",
        "jiyou i need you", "need you jiyou",
    ]

    name_responses = [
        "Yes? How can I help you?",
        "I'm here! What do you need?",
        "That's me! What's up?",
        "You called? How can I assist?",
        "Hello! What can I do for you?",
        "At your service! What's on your mind?",
        "Present! How may I help?",
    ]

    for phrase in name_phrases:
        if phrase not in used:
            used.add(phrase)
            items.append(create_item(f"name_{item_num:04d}", phrase, random.choice(name_responses), "name"))
            item_num += 1

    return items


def generate_318_test_inputs() -> List[Dict]:
    """Generate test/debug variations."""
    items = []
    item_num = 1
    used = set()

    test_phrases = [
        "test", "Test", "TEST", "test!", "testing",
        "Testing", "TESTING", "testing 123", "test 123",
        "test test", "testing testing", "test test test",
        "1 2 3", "123", "one two three", "1234567890",
        "hello?", "Hello?", "hello???", "anyone?",
        "anyone there", "anyone there?", "anybody there",
        "is anyone there", "is anybody there", "anyone home",
        "can you hear me", "can you see this", "can u hear me",
        "are you there", "you there", "u there", "there?",
        "working", "is it working", "does this work",
        "check", "checking", "mic check", "sound check",
        "echo", "ping", "pong", "hello hello",
        "am i connected", "connection test", "connectivity",
        "are you online", "you online", "u online",
        "are you awake", "you awake", "u awake",
        "are you alive", "alive?", "still alive",
        "respond", "respond please", "say something",
        "talk to me", "speak", "speak up", "say hi",
        "is this on", "is this thing on", "hello world",
        "this is a test", "just testing", "only a test",
    ]

    for phrase in test_phrases:
        if phrase not in used:
            used.add(phrase)
            items.append(create_item(f"test_{item_num:04d}", phrase, random.choice(TEST_RESPONSES), "test"))
            item_num += 1

    return items


def generate_319_random_inputs() -> List[Dict]:
    """Generate random/edge case variations."""
    items = []
    item_num = 1
    used = set()

    random_phrases = [
        # Keyboard smash
        "asdf", "ASDF", "qwerty", "zxcv", "jkl",
        "aaa", "bbb", "xxx", "zzz", "abc",
        "asdfgh", "qwertyuiop", "zxcvbnm",
        "askdjfhaklsjdfh", "sdkjfhskdjf",

        # Punctuation
        "...", "....", ".....", "......",
        "---", "___", "***", "###",
        "!", "!!", "!!!", "!?", "?!", "!?!",
        "?", "??", "???", "????",
        ".", "..", "...?",
        "~", "~~", "~~~",
        ";", ";;", ";;;",

        # Internet speak
        "lol", "LOL", "lmao", "LMAO", "rofl", "ROFL",
        "haha", "hehe", "hihi", "hoho",
        "xD", "XD", ":)", ":(", ":P", ":D", ";)", "^_^",
        "bruh", "bro", "dude", "fam",
        "lel", "kek", "gg", "GG", "ez", "EZ",
        "rip", "RIP", "oof", "OOF",
        "yeet", "skrt", "ree", "reee",
        "based", "cringe", "sus", "SUS",
        "pog", "poggers", "pogchamp", "sadge",
        "uwu", "owo", "UwU", "OwO",
        "nyaa", "meow", "woof", "rawr",

        # Fillers
        "blah", "blah blah", "blahblahblah",
        "meh", "eh", "ugh", "hmph",
        "idk", "idc", "idgaf",
        "whatever", "whatevs", "whatev",

        # Random
        "random", "gibberish", "nonsense",
        "aaaaaaa", "AAAAAA", "eeeeee",
        "spam", "spamspam", "spamspamspam",
        "abcdefg", "abcdefghijklmnop",
        "nothing", "something", "anything",
        "stuff", "things", "words",
        "beep", "boop", "beep boop",
        "la la la", "lalala", "tra la la",
        "yadda yadda", "blah de blah",
        "herp derp", "derp", "hurr durr",
    ]

    for phrase in random_phrases:
        if phrase not in used:
            used.add(phrase)
            items.append(create_item(f"random_{item_num:04d}", phrase, random.choice(RANDOM_INPUT_RESPONSES), "random"))
            item_num += 1

    return items


def save_lesson(filename: str, lesson: Dict) -> int:
    """Save a lesson to file and return item count."""
    filepath = os.path.join(LESSONS_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(lesson, f, indent=2, ensure_ascii=False)
    return len(lesson['items'])


def main():
    """Generate all simple conversation lessons."""
    random.seed(42)

    total_items = 0

    lessons = [
        ("300_simple_greetings.json", "Simple Greetings", "Simple greeting variations", generate_300_simple_greetings),
        ("301_simple_farewells.json", "Simple Farewells", "Simple farewell variations", generate_301_simple_farewells),
        ("302_simple_questions.json", "Simple Questions", "What's up and how are you variations", generate_302_simple_questions),
        ("303_identity_questions.json", "Identity Questions", "Who/what are you questions", generate_303_identity_questions),
        ("304_help_requests.json", "Help Requests", "Help request variations", generate_304_help_requests),
        ("305_acknowledgments.json", "Acknowledgments", "OK, sure, got it variations", generate_305_acknowledgments),
        ("306_emotional_responses.json", "Emotional Responses", "Emotional state expressions", generate_306_emotional_responses),
        ("307_small_talk_weather.json", "Weather Small Talk", "Weather-related conversation", generate_307_small_talk_weather),
        ("308_small_talk_time.json", "Time Greetings", "Time-based greetings", generate_308_small_talk_time),
        ("309_capability_questions.json", "Capability Questions", "Can you X questions", generate_309_capability_questions),
        ("310_opinion_requests.json", "Opinion Requests", "What do you think variations", generate_310_opinion_requests),
        ("311_clarification.json", "Clarification", "What? Huh? variations", generate_311_clarification),
        ("312_affirmations.json", "Affirmations", "Yes/no/maybe variations", generate_312_affirmations),
        ("313_casual_fillers.json", "Casual Fillers", "Um, well, so variations", generate_313_casual_fillers),
        ("314_exclamations.json", "Exclamations", "Wow, cool, awesome variations", generate_314_exclamations),
        ("315_negative_responses.json", "Negative Responses", "No thanks, pass variations", generate_315_negative_responses),
        ("316_courtesy.json", "Courtesy Phrases", "Thanks, please, sorry variations", generate_316_courtesy),
        ("317_name_variations.json", "Name Variations", "Jiyou name variations", generate_317_name_variations),
        ("318_test_inputs.json", "Test Inputs", "Test, hello? variations", generate_318_test_inputs),
        ("319_random_inputs.json", "Random Inputs", "Edge cases and random inputs", generate_319_random_inputs),
    ]

    print("Generating simple conversation lessons...")
    print("-" * 50)

    for filename, title, description, generator in lessons:
        items = generator()
        lesson = create_lesson(
            filename.replace('.json', '').replace('_', '-'),
            f"Dialogue: {title}",
            description,
            items
        )
        count = save_lesson(filename, lesson)
        total_items += count
        print(f"{filename}: {count} items")

    print("-" * 50)
    print(f"Total items generated: {total_items}")
    print(f"\nLessons saved to: {LESSONS_DIR}")
    print("\nRemember to update manifest.json with the new lessons!")


if __name__ == "__main__":
    main()
