import google.generativeai as genai
import os
from typing import List, Dict, Any
from src.models.products import Product
from src.models.review import Review

class LLMService:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')

    def summarize_reviews(self, product: Product, reviews: List[Review]) -> str:
        """
        Summarize product reviews using Gemini AI.
        """
        if not reviews:
            return "No reviews available for this product."

        # Prepare review text
        review_texts = []
        for review in reviews:
            review_texts.append(f"Rating: {review.rating}/5\nComment: {review.comment}")

        reviews_text = "\n\n".join(review_texts)

        prompt = f"""
        Summarize the following customer reviews for the product "{product.name}".
        Provide a concise summary highlighting key points, overall sentiment, common praises, and criticisms.
        Include average rating if possible.

        Reviews:
        {reviews_text}

        Summary:
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Error generating summary: {str(e)}"

    def answer_question(self, product: Product, reviews: List[Review], question: str) -> str:
        """
        Answer questions about the product using Gemini AI, based on product details and reviews.
        """
        # Prepare product context
        product_context = f"""
        Product Name: {product.name}
        Description: {product.description or 'No description available'}
        Price: ${product.price}
        Category: {product.category.name if product.category else 'N/A'}
        Stock: {product.stock}
        """

        # Prepare review context (limit to recent/top reviews for context length)
        review_context = ""
        if reviews:
            top_reviews = reviews[:10]  # Limit to 10 reviews to avoid token limits
            review_texts = []
            for review in top_reviews:
                review_texts.append(f"Rating: {review.rating}/5 - {review.comment}")
            review_context = "\n".join(review_texts)
        else:
            review_context = "No reviews available."

        prompt = f"""
        Answer the following question about the product based on the provided product details and customer reviews.
        Be helpful, accurate, and concise. If the information is not available in the context, say so politely.

        Product Details:
        {product_context}

        Customer Reviews:
        {review_context}

        Question: {question}

        Answer:
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Error generating answer: {str(e)}"
