
# This service will handle the topic entry and initiate the CrewAI agents' search for books related to the topic, as well as the organization of those books into a course structure.

# CrewAI integration for course generation
# def generate_course_from_topic(topic: str):

from backend.app.agents.crews.crew import create_crew

class CourseGenerationService:
	"""
	Service for generating a course structure from a topic using CrewAI agents.
	"""
	def __init__(self):
		pass

	def generate_course_from_topic(self, topic: str):
		"""
		Given a topic, use CrewAI agents to research books and generate a course structure.
		Returns the course structure as produced by the CrewAI pipeline.
		"""
		crew = create_crew(topic)
		result = crew.kickoff(inputs={"topic": topic})
		return result

