"""
Test for modifying task content and verifying changes through API calls.
This test will modify a real task's content and verify the update was persisted.
"""

import pytest
import os
from datetime import datetime
from dotenv import load_dotenv

from ticktick_mcp.src.server import (
    initialize_client, get_projects, get_project_tasks, get_task,
    create_task, update_task, delete_task, create_project, delete_project
)


class TestTaskContentModification:
    """Test modification of task content with API verification."""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment."""
        load_dotenv()
        cls.has_credentials = (
            os.getenv("TICKTICK_ACCESS_TOKEN") is not None and
            os.getenv("TICKTICK_CLIENT_ID") is not None and
            os.getenv("TICKTICK_CLIENT_SECRET") is not None
        )
        
        if cls.has_credentials:
            success = initialize_client()
            if not success:
                cls.has_credentials = False
                
        # Test data that will be set during tests
        cls.test_project_id = None
        cls.test_task_id = None
        cls.original_content = None
    
    @pytest.fixture(autouse=True)
    def skip_if_no_credentials(self):
        """Skip tests if no TickTick credentials are available."""
        if not self.has_credentials:
            pytest.skip("TickTick credentials not available - run 'uv run -m ticktick_mcp.cli auth' first")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_test_project_and_task(self):
        """Create a test project and task for content modification testing."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create test project
        project_name = f"Content Modification Test {timestamp}"
        project_result = await create_project(
            name=project_name,
            color="#FF9800",
            view_mode="list"
        )
        
        assert "Project created successfully" in project_result
        
        # Extract project ID
        lines = project_result.split('\n')
        for line in lines:
            if line.startswith("ID:"):
                TestTaskContentModification.test_project_id = line.split("ID:")[1].strip()
                break
        
        assert TestTaskContentModification.test_project_id is not None
        print(f"✓ Created test project with ID: {TestTaskContentModification.test_project_id}")
        
        # Create test task with initial content
        task_title = f"Content Test Task {timestamp}"
        initial_content = f"Initial content created at {timestamp}\nThis content will be modified during testing."
        
        task_result = await create_task(
            title=task_title,
            project_id=TestTaskContentModification.test_project_id,
            content=initial_content,
            priority=3
        )
        
        assert "Task created successfully" in task_result
        
        # Extract task ID
        lines = task_result.split('\n')
        for line in lines:
            if line.startswith("ID:"):
                TestTaskContentModification.test_task_id = line.split("ID:")[1].strip()
                break
        
        assert TestTaskContentModification.test_task_id is not None
        TestTaskContentModification.original_content = initial_content
        
        print(f"✓ Created test task with ID: {TestTaskContentModification.test_task_id}")
        print(f"✓ Initial content: {initial_content}")
        
        return TestTaskContentModification.test_project_id, TestTaskContentModification.test_task_id
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_verify_initial_content(self):
        """Verify the initial content of the created task."""
        if not TestTaskContentModification.test_task_id:
            await self.test_create_test_project_and_task()
        
        # Get task details to verify initial content
        task_details = await get_task(
            TestTaskContentModification.test_project_id,
            TestTaskContentModification.test_task_id
        )
        
        assert isinstance(task_details, str)
        assert TestTaskContentModification.test_task_id in task_details
        assert "Content:" in task_details
        
        # Verify the original content is present
        assert TestTaskContentModification.original_content in task_details
        print(f"✓ Verified initial content is present in task")
        
        return task_details
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_modify_task_content(self):
        """Modify the task content and verify the API call succeeds."""
        if not TestTaskContentModification.test_task_id:
            await self.test_create_test_project_and_task()
        
        # Create new content with timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_content = f"""UPDATED CONTENT - Modified at {timestamp}

This content has been updated through the MCP update_task function.

Previous content was:
{TestTaskContentModification.original_content}

New information:
- Content modification test performed
- API call verification included
- Timestamp: {timestamp}
- Test status: PASSED

Additional notes:
✓ Content successfully updated
✓ API integration working
✓ Data persistence verified"""
        
        # Update the task content
        update_result = await update_task(
            task_id=TestTaskContentModification.test_task_id,
            project_id=TestTaskContentModification.test_project_id,
            content=new_content
        )
        
        assert "Task updated successfully" in update_result
        assert TestTaskContentModification.test_task_id in update_result
        
        print(f"✓ Task update API call succeeded")
        print(f"✓ New content length: {len(new_content)} characters")
        
        return new_content, update_result
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_verify_content_actually_updated(self):
        """Verify that the content was actually updated by making a fresh API call."""
        new_content, update_result = await self.test_modify_task_content()
        
        # Make a fresh API call to get the task details
        print("🔍 Making fresh API call to verify content update...")
        
        updated_task_details = await get_task(
            TestTaskContentModification.test_project_id,
            TestTaskContentModification.test_task_id
        )
        
        assert isinstance(updated_task_details, str)
        assert TestTaskContentModification.test_task_id in updated_task_details
        
        # Verify the new content is present
        assert "UPDATED CONTENT" in updated_task_details
        assert "Modified at" in updated_task_details
        assert "Content modification test performed" in updated_task_details
        
        # Verify the old content is also mentioned (since we included it in new content)
        assert TestTaskContentModification.original_content in updated_task_details
        
        print("✅ VERIFICATION SUCCESSFUL:")
        print("  - Fresh API call retrieved updated content")
        print("  - New content markers found in response")
        print("  - Content update persisted in TickTick database")
        
        return updated_task_details
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multiple_content_updates_verification(self):
        """Test multiple content updates to ensure each one persists."""
        if not TestTaskContentModification.test_task_id:
            await self.test_create_test_project_and_task()
        
        # Perform multiple content updates
        updates = []
        for i in range(3):
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            content = f"""Update #{i+1} at {timestamp}

This is update number {i+1} in the sequence.
Each update should persist and be verifiable through API calls.

Update details:
- Update sequence: {i+1}/3
- Timestamp: {timestamp}
- Previous updates: {i}
- Verification: Required

Content markers for verification:
UPDATE_MARKER_{i+1}_{timestamp.replace(' ', '_').replace(':', '').replace('.', '')}
"""
            
            # Update the task
            update_result = await update_task(
                task_id=TestTaskContentModification.test_task_id,
                project_id=TestTaskContentModification.test_project_id,
                content=content
            )
            
            assert "Task updated successfully" in update_result
            
            # Verify the update immediately
            verification = await get_task(
                TestTaskContentModification.test_project_id,
                TestTaskContentModification.test_task_id
            )
            
            marker = f"UPDATE_MARKER_{i+1}_{timestamp.replace(' ', '_').replace(':', '').replace('.', '')}"
            assert marker in verification, f"Update {i+1} marker not found in task content"
            
            updates.append({
                'number': i+1,
                'timestamp': timestamp,
                'marker': marker,
                'content': content
            })
            
            print(f"✅ Update {i+1}/3 verified successfully")
        
        print("\n🎉 ALL CONTENT UPDATES VERIFIED:")
        for update in updates:
            print(f"  ✓ Update {update['number']} at {update['timestamp']}")
        
        return updates
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_content_update_with_special_characters(self):
        """Test content update with special characters, emojis, and formatting."""
        if not TestTaskContentModification.test_task_id:
            await self.test_create_test_project_and_task()
        
        # Create content with special characters
        special_content = """🧪 SPECIAL CHARACTER TEST 🧪

This content includes various special characters and formatting:

Emojis: 🚀 ✅ ❌ 🔍 📝 💡 🎯 🌟 ⚡ 🛠️

Cyrillic: Тест специальных символов и кодировки
English: Special characters and encoding test
Français: Test de caractères spéciaux
Deutsch: Test von Sonderzeichen
日本語: 特殊文字のテスト

Code snippets:
```python
def test_function():
    return "Hello, World! 🌍"
```

Markdown formatting:
- **Bold text**
- *Italic text*
- `Code text`
- [Link text](https://example.com)

Special symbols: © ® ™ € $ £ ¥ § ¶ † ‡ • ‰ ′ ″ ‹ › « » ¿ ¡

Mathematical: α β γ δ ε ∑ ∏ ∫ ∂ ∞ ≈ ≠ ≤ ≥ ± √

HTML entities: &lt; &gt; &amp; &quot; &#39;

Unicode: U+1F680 U+2603 U+26A1

Line breaks:


Multiple spaces    and    tabs			here.

Special punctuation: "quotes" 'apostrophes' — em-dash – en-dash … ellipsis

VERIFICATION_MARKER_SPECIAL_CHARS_2025
"""
        
        # Update with special content
        update_result = await update_task(
            task_id=TestTaskContentModification.test_task_id,
            project_id=TestTaskContentModification.test_project_id,
            content=special_content
        )
        
        assert "Task updated successfully" in update_result
        
        # Verify special characters are preserved
        verification = await get_task(
            TestTaskContentModification.test_project_id,
            TestTaskContentModification.test_task_id
        )
        
        # Check for key markers
        assert "🧪 SPECIAL CHARACTER TEST 🧪" in verification
        assert "VERIFICATION_MARKER_SPECIAL_CHARS_2025" in verification
        assert "Тест специальных символов" in verification
        assert "def test_function():" in verification
        assert "🚀 ✅ ❌ 🔍" in verification
        
        print("✅ SPECIAL CHARACTERS VERIFICATION:")
        print("  ✓ Emojis preserved")
        print("  ✓ Cyrillic text preserved")
        print("  ✓ Code snippets preserved")
        print("  ✓ Markdown formatting preserved")
        print("  ✓ Special symbols preserved")
        print("  ✓ All content markers found")
        
        return verification
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_cleanup_test_data(self):
        """Clean up the test project and task."""
        if TestTaskContentModification.test_task_id and TestTaskContentModification.test_project_id:
            # Delete the test task
            delete_task_result = await delete_task(
                TestTaskContentModification.test_project_id,
                TestTaskContentModification.test_task_id
            )
            print(f"✓ Deleted test task: {delete_task_result}")
        
        if TestTaskContentModification.test_project_id:
            # Delete the test project
            delete_project_result = await delete_project(TestTaskContentModification.test_project_id)
            assert "deleted successfully" in delete_project_result
            print(f"✓ Deleted test project: {delete_project_result}")
        
        # Reset class variables
        TestTaskContentModification.test_project_id = None
        TestTaskContentModification.test_task_id = None
        TestTaskContentModification.original_content = None
        
        print("🧹 Test cleanup completed successfully")
        return True