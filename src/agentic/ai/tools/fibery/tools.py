import asyncio
import logging
from typing import Any

from pydantic_ai import FunctionToolset, RunContext

from agentic.ai.agents.email.schema import EmailRubricUpdate

from .deps import FiberyDeps
from .graphql_client import Client

logger = logging.getLogger(__name__)

# Initializes Fibery Toolset collection
fibery_toolset = FunctionToolset()


@fibery_toolset.tool(retries=2)  # ty: ignore[invalid-argument-type]
async def get_emails(ctx: RunContext[FiberyDeps]) -> list[dict[str, Any]]:
    """Fetches the user's emails from Fibery.

    Returns:
        A list of email dictionaries containing publicId, name, date, email, message body, etc.
    """
    logger.info("Fetching emails from Fibery...")
    try:
        async with ctx.deps.get_client() as client:
            result = await client.get_emails()

        if result.find_emails:
            # Filter out None objects and dump to dictionaries
            emails_list = [
                email.model_dump() for email in result.find_emails if email is not None
            ]
            logger.info("Successfully %s fetched emails.", len(emails_list))
            return emails_list
        logger.info("No emails found.")
        return []
    except Exception as e:
        logger.exception("Failed to fetch emails")
        # Raise or return error representation so LLM understands what went wrong
        raise RuntimeError(f"Failed to fetch emails: {e!s}")


@fibery_toolset.tool(retries=2)  # ty: ignore[invalid-argument-type]
async def update_emails(
    ctx: RunContext[FiberyDeps], updates: list[EmailRubricUpdate]
) -> str:
    """Updates the rubric/importance score for multiple emails in Fibery concurrently.

    Enforces safe concurrency limits using an asyncio.Semaphore to prevent rate limits
    and resource exhaustion.

    Args:
          ctx: Run context providing the Fibery dependency container.
          updates: Email updates containing the publicId and mapped rubric score.
    """
    if not updates:
        logger.info("No email updates provided.")
        return "No emails to update."

    logger.info(
        "Initiating rate-limited concurrent update of %s emails...",
        len(updates),
    )

    # Limit maximum concurrent requests to 10
    semaphore = asyncio.Semaphore(10)

    async def sem_update(cl: Client, update: EmailRubricUpdate):
        async with semaphore:
            return await cl.update_email_rubric(
                public_id=update.public_id, rubric=update.rubric
            )

    try:
        async with ctx.deps.get_client() as client:
            tasks = [sem_update(client, update) for update in updates]
            # Gather tasks and return exceptions gracefully to prevent entire process crash
            results = await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logger.exception("Failed to execute updates")
        return f"Failed to execute updates: {e!s}"

    success_count = 0
    failure_details = []

    for update, result in zip(updates, results):
        if isinstance(result, Exception):
            err_msg = f"Failed to update public_id={update.public_id}: {result!s}"
            logger.error(err_msg)
            failure_details.append(err_msg)
        else:
            success_count += 1
            logger.debug(
                "Successfully updated public_id=%s with rubric=%s",
                update.public_id,
                update.rubric,
            )

    summary = f"Successfully updated {success_count}/{len(updates)} emails."
    if failure_details:
        summary += f" Errors encountered: {'; '.join(failure_details)}"

    logger.info(summary)
    return summary
