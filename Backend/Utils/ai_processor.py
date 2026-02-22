import re

def analyze_complaint(text):
    """
    Analyze complaint text using NLP to extract:
    - Question number
    - Issue summary
    - Issue type
    - Detailed faculty explanation
    - Confidence score
    
    Args:
        text (str): Complaint text from student
        
    Returns:
        dict: Extracted information with detailed explanation
    """
    try:
        text_lower = text.lower()
        
        # Extract question number using regex
        question_number = extract_question_number(text)
        
        # Detect issue type
        issue_type = detect_issue_type(text_lower)
        
        # Generate summary
        summary = generate_summary(text, question_number, issue_type)
        
        # Generate detailed faculty explanation
        detailed_explanation = generate_detailed_explanation(
            text, question_number, issue_type, text_lower
        )
        
        # Calculate confidence score
        confidence_score = calculate_confidence_score(
            text, question_number, issue_type
        )
        
        return {
            'question_number': question_number,
            'summary': summary,
            'issue_type': issue_type,
            'detailed_explanation': detailed_explanation,
            'confidence_score': confidence_score
        }
    except Exception as e:
        # Fallback to basic extraction on error
        return {
            'question_number': 'Unknown',
            'summary': 'Error processing complaint',
            'issue_type': 'General Complaint',
            'detailed_explanation': f'Unable to process complaint automatically. Manual review required. Error: {str(e)}',
            'confidence_score': 0.0
        }

def extract_question_number(text):
    """Extract question number from complaint text"""
    # Pattern 1: Q1, Q2, Q3, etc.
    pattern1 = re.search(r'\bQ\.?\s*(\d+)\b', text, re.IGNORECASE)
    if pattern1:
        return f"Q{pattern1.group(1)}"
    
    # Pattern 2: Question 1, Question 2, etc.
    pattern2 = re.search(r'\bquestion\s+(\d+)\b', text, re.IGNORECASE)
    if pattern2:
        return f"Q{pattern2.group(1)}"
    
    # Pattern 3: #1, #2, etc.
    pattern3 = re.search(r'#(\d+)', text)
    if pattern3:
        return f"Q{pattern3.group(1)}"
    
    # Pattern 4: Standalone numbers in context
    pattern4 = re.search(r'\b(\d+)[a-z]?\s*(?:marks?|points?)', text, re.IGNORECASE)
    if pattern4:
        return f"Q{pattern4.group(1)}"
    
    return "Unknown"

def detect_issue_type(text_lower):
    """Detect the type of issue from complaint text"""
    # Keywords for different issue types
    marks_keywords = ['marks', 'mark', 'points', 'score', 'grade', 'missing', 'deducted', 'deserve']
    evaluation_keywords = ['wrong', 'incorrect', 'unfair', 'mistake', 'error', 'wrongly', 'incorrectly']
    partial_keywords = ['partial', 'some', 'part', 'section', 'step']
    unchecked_keywords = ['not checked', 'unchecked', 'not evaluated', 'skipped', 'missed', 'overlooked']
    calculation_keywords = ['calculation', 'total', 'totaling', 'sum', 'add', 'adding', 'counted']
    
    # Check for unchecked question (highest priority)
    if any(keyword in text_lower for keyword in unchecked_keywords):
        return "Unchecked Question"
    
    # Check for calculation error
    if any(keyword in text_lower for keyword in calculation_keywords):
        return "Calculation Error"
    
    # Check for marks discrepancy
    if any(keyword in text_lower for keyword in marks_keywords):
        if any(keyword in text_lower for keyword in partial_keywords):
            return "Partial Marks Issue"
        return "Marks Discrepancy"
    
    # Check for evaluation error
    if any(keyword in text_lower for keyword in evaluation_keywords):
        return "Evaluation Issue"
    
    return "General Complaint"

def generate_summary(text, question_number, issue_type):
    """Generate a concise summary of the complaint"""
    # Truncate text if too long
    text_snippet = text[:150] + "..." if len(text) > 150 else text
    
    if question_number != "Unknown":
        summary = f"Student reports {issue_type.lower()} in {question_number}. "
    else:
        summary = f"Student reports {issue_type.lower()}. "
    
    # Extract key phrases
    if "deserve" in text.lower():
        summary += "Claims deserving more marks. "
    if "correct" in text.lower() and "answer" in text.lower():
        summary += "States answer is correct. "
    if "not checked" in text.lower() or "unchecked" in text.lower():
        summary += "Claims answer not properly checked. "
    
    return summary.strip()

# Optional: Placeholder for future OpenAI integration
def analyze_with_openai(text):
    """
    Placeholder for OpenAI API integration
    Uncomment and configure when API key is available
    """
    # import openai
    # openai.api_key = "your-api-key"
    # 
    # response = openai.ChatCompletion.create(
    #     model="gpt-3.5-turbo",
    #     messages=[
    #         {"role": "system", "content": "Extract question number and summarize complaint"},
    #         {"role": "user", "content": text}
    #     ]
    # )
    # return response.choices[0].message.content
    pass


def generate_detailed_explanation(text, question_number, issue_type, text_lower):
    """
    Generate structured, detailed explanation for faculty
    
    Args:
        text (str): Original complaint text
        question_number (str): Extracted question number
        issue_type (str): Detected issue type
        text_lower (str): Lowercase version of text
        
    Returns:
        str: Formatted detailed explanation
    """
    # Section 1: Complaint Overview
    overview = f"**Complaint Overview:**\n"
    if question_number != "Unknown":
        overview += f"The student has raised a concern regarding {question_number} of the examination paper. "
    else:
        overview += "The student has raised a concern regarding the examination evaluation. "
    
    # Add context about the complaint
    if len(text) > 100:
        overview += "The complaint provides detailed information about the perceived issue."
    else:
        overview += "The complaint is brief but indicates a specific concern."
    
    # Section 2: Identified Issue
    identified_issue = f"\n\n**Identified Issue:**\n{issue_type}."
    
    # Section 3: AI Interpretation
    interpretation = "\n\n**AI Interpretation:**\n"
    
    if issue_type == "Marks Discrepancy":
        interpretation += "The student believes that the marks awarded do not accurately reflect their performance. "
        if 'deserve' in text_lower or 'should' in text_lower:
            interpretation += "The student explicitly states they deserve more marks. "
        if 'correct' in text_lower:
            interpretation += "The student claims their answer is correct. "
        if any(word in text_lower for word in ['missing', 'deducted', 'lost']):
            interpretation += "There appears to be a concern about marks being incorrectly deducted or not awarded. "
    
    elif issue_type == "Unchecked Question":
        interpretation += "The student believes that this question was not properly evaluated or was completely overlooked during marking. "
        interpretation += "This requires immediate verification of the answer sheet to confirm if the question was graded. "
    
    elif issue_type == "Calculation Error":
        interpretation += "The student suspects an error in the calculation or totaling of marks. "
        interpretation += "This may involve incorrect addition of marks across different sections or questions. "
    
    elif issue_type == "Evaluation Issue":
        interpretation += "The student believes the evaluation methodology or marking scheme was not correctly applied. "
        if 'method' in text_lower or 'approach' in text_lower:
            interpretation += "The concern relates to the method or approach used in solving the problem. "
        if 'step' in text_lower:
            interpretation += "The student mentions specific steps that may not have been properly credited. "
    
    elif issue_type == "Partial Marks Issue":
        interpretation += "The student believes they should receive partial credit for their work. "
        interpretation += "The answer may be partially correct or demonstrate understanding of the concept. "
    
    else:
        interpretation += "The complaint requires manual review to understand the specific concern raised by the student. "
    
    # Add specific details from complaint
    if 'formula' in text_lower:
        interpretation += "The student mentions formula usage. "
    if 'diagram' in text_lower or 'graph' in text_lower:
        interpretation += "The complaint involves diagrams or graphical representations. "
    if 'explanation' in text_lower or 'reasoning' in text_lower:
        interpretation += "The student provided explanations or reasoning in their answer. "
    
    # Section 4: Suggested Faculty Action
    suggested_action = "\n\n**Suggested Faculty Action:**\n"
    
    if question_number != "Unknown":
        suggested_action += f"It is recommended that the faculty re-evaluate {question_number}, "
    else:
        suggested_action += "It is recommended that the faculty review the relevant section, "
    
    if issue_type == "Marks Discrepancy":
        suggested_action += "specifically verifying step marking and method correctness according to the marking scheme. "
        suggested_action += "Compare the student's answer with the model answer and ensure all valid approaches are credited."
    
    elif issue_type == "Unchecked Question":
        suggested_action += "first confirming whether the question was evaluated. "
        suggested_action += "If unevaluated, complete the marking process. If evaluated, verify the marks were correctly recorded."
    
    elif issue_type == "Calculation Error":
        suggested_action += "recalculating the total marks to ensure accuracy. "
        suggested_action += "Verify that all section marks have been correctly added and recorded."
    
    elif issue_type == "Evaluation Issue":
        suggested_action += "reviewing the evaluation criteria and ensuring the marking scheme was consistently applied. "
        suggested_action += "Consider alternative valid approaches that may have been used by the student."
    
    elif issue_type == "Partial Marks Issue":
        suggested_action += "assessing whether partial credit is warranted based on the work shown. "
        suggested_action += "Review the marking scheme for partial credit allocation guidelines."
    
    else:
        suggested_action += "carefully reviewing the student's answer and the complaint details. "
        suggested_action += "Consult with colleagues if the issue requires subject matter expertise."
    
    # Combine all sections
    detailed_explanation = overview + identified_issue + interpretation + suggested_action
    
    return detailed_explanation

def calculate_confidence_score(text, question_number, issue_type):
    """
    Calculate confidence score for AI analysis
    
    Args:
        text (str): Complaint text
        question_number (str): Extracted question number
        issue_type (str): Detected issue type
        
    Returns:
        float: Confidence score between 0 and 1
    """
    score = 0.5  # Base score
    
    # Increase confidence if question number is detected
    if question_number != "Unknown":
        score += 0.2
    
    # Increase confidence based on text length (more context = higher confidence)
    if len(text) > 150:
        score += 0.15
    elif len(text) > 80:
        score += 0.10
    elif len(text) > 40:
        score += 0.05
    
    # Increase confidence if issue type is specific (not general)
    if issue_type != "General Complaint":
        score += 0.15
    
    # Increase confidence if complaint contains specific keywords
    text_lower = text.lower()
    specific_keywords = ['marks', 'question', 'answer', 'correct', 'wrong', 'error', 'deserve']
    keyword_count = sum(1 for keyword in specific_keywords if keyword in text_lower)
    score += min(keyword_count * 0.02, 0.10)
    
    # Cap at 0.95 (never 100% confident in automated analysis)
    return min(score, 0.95)

# Optional: Placeholder for future OpenAI integration
def analyze_with_openai(text):
    """
    Placeholder for OpenAI API integration
    Uncomment and configure when API key is available
    """
    # import openai
    # import json
    # 
    # openai.api_key = "your-api-key"
    # 
    # prompt = f"""You are an academic grievance assistant. Convert the student's complaint into a structured faculty-oriented explanation.
    # 
    # Student Complaint: {text}
    # 
    # Extract and provide:
    # 1. Question number (if mentioned)
    # 2. Issue type (Marks Discrepancy, Calculation Error, Unchecked Question, Evaluation Issue, or General Complaint)
    # 3. Brief summary
    # 4. Detailed faculty-oriented explanation with sections: Complaint Overview, Identified Issue, AI Interpretation, Suggested Faculty Action
    # 5. Confidence score (0-1)
    # 
    # Respond strictly in JSON format:
    # {{
    #     "question_number": "Q3",
    #     "issue_type": "Marks Discrepancy",
    #     "summary": "Brief summary",
    #     "detailed_explanation": "Detailed explanation",
    #     "confidence_score": 0.87
    # }}
    # """
    # 
    # try:
    #     response = openai.ChatCompletion.create(
    #         model="gpt-3.5-turbo",
    #         messages=[
    #             {"role": "system", "content": "You are an academic grievance analysis assistant."},
    #             {"role": "user", "content": prompt}
    #         ],
    #         temperature=0.3
    #     )
    #     
    #     result = json.loads(response.choices[0].message.content)
    #     return result
    # except Exception as e:
    #     print(f"OpenAI API error: {e}")
    #     return None
    pass
