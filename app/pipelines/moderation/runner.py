## app\pipelines\moderation\runner.py

from app.pipelines.moderation import (
    ModerationRules,
    TextPreprocessor, 
    AIClassifier,
    DecisionEngine, 
    HITLHandler
)

class ModerationPipeline:
    @classmethod
    def process_issue(cls, issue_data: dict) -> dict:
        ## Main entry for the Celery worker

        title = issue_data.get("title", "")
        description = issue_data.get("description", "")
        images = issue_data.get("images", [])

        ## 1. PreProcessing
        prep_result = TextPreprocessor.preprocess(title, description)

        ## 2. Rules Engine

        rules_result = ModerationRules.run_all_checks(
            prep_result["clean_title"],
            prep_result["clean_description"]
        )

        ## 3. AI classification
        """
        We pass the result even if rules failed because we might want the data for logging
        """

        ai_result = AIClassifier.classify(
            prep_result["clean_title"], 
            prep_result["clean_description"], 
            images
        )

        # 4. Final Decision
        decision_result = DecisionEngine.make_decision(
            rules_result, 
            prep_result, 
            ai_result
        )
        
        return {
            "issue_id": issue_data.get("id"),
            "pipeline_version": "1.0",
            "results": {
                "rules": rules_result,
                "ai": ai_result,
                "decision": decision_result
            }
        }

