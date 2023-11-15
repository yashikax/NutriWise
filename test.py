from transformers import pipeline
classifier = pipeline("text-classification",model='bhadresh-savani/distilbert-base-uncased-emotion', top_k=None)
prediction = classifier("I am feeling neither upset nor happy!")
print(prediction)