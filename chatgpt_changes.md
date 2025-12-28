# ChatGPT Sync
Repo: chatgpt-team
Base: origin/main
Base commit (merge-base): ff7a0e267ecf77d0c22177f2f47aba47f26328df
Dirs: app tests static schemas src scripts/src
Root files: project-tree.md pyproject.toml chatgpt_sync.sh AGENTS.md __init__.py generate_tree.py
Mode: changes
Generated: 2025-12-28T19:31:23+07:00

## CHANGE SUMMARY (since ff7a0e267ecf77d0c22177f2f47aba47f26328df, includes worktree)

```
M	project-tree.md
```

## PATCH (since ff7a0e267ecf77d0c22177f2f47aba47f26328df, includes worktree)

```diff
diff --git a/project-tree.md b/project-tree.md
index a98ddd6..e0fe8bd 100755
--- a/project-tree.md
+++ b/project-tree.md
@@ -18,6 +18,7 @@
   📄 pytest.ini
   📄 render.yaml
   📄 requirements.txt
+  📁 .codex
   📁 app
     📄 __init__.py
     📄 http_client.py
@@ -107,6 +108,7 @@
     📄 __init__.py
     📄 openapi.yaml
   📁 scripts
+    📄 README.md
     📄 batch_download_test.sh
     📄 content_endpoints_smoke.sh
     📄 images_variations_smoke.sh
@@ -118,7 +120,7 @@
     📄 sse_smoke_test.sh
     📄 test_local.sh
     📄 test_render.sh
-    📄 test_success_gates_integration.sh
+    📄 test_success_gates_integration.py
     📄 uploads_e2e_test.sh
   📁 static
     📁 .well-known
```

## CURRENT CONTENT OF CHANGED FILES (WORKTREE)

## FILE: project-tree.md @ WORKTREE
```
  📄 .env.env
  📄 .env.example.env
  📄 .gitattributes
  📄 .gitignore
  📄 .gitleaks.toml
  📄 AGENTS.md
  📄 ChatGPT-API_reference_ground_truth-2025-10-29.pdf
  📄 RELAY_CHECKLIST_v16.md
  📄 RELAY_PROGRESS_SUMMARY_v12.md
  📄 __init__.py
  📄 chatgpt_baseline.md
  📄 chatgpt_changes.md
  📄 chatgpt_sync.sh
  📄 generate_tree.py
  📄 input.png
  📄 openai_models_2025-11.csv
  📄 project-tree.md
  📄 pytest.ini
  📄 render.yaml
  📄 requirements.txt
  📁 .codex
  📁 app
    📄 __init__.py
    📄 http_client.py
    📄 main.py
    📁 api
      📄 __init__.py
      📄 forward_openai.py
      📄 routes.py
      📄 sse.py
      📄 tools_api.py
    📁 core
      📄 __init__.py
      📄 config.py
      📄 http_client.py
      📄 logging.py
      📄 settings.py
    📁 manifests
      📄 __init__.py
      📄 tools_manifest.json
    📁 middleware
      📄 __init__.py
      📄 p4_orchestrator.py
      📄 relay_auth.py
      📄 validation.py
    📁 models
      📄 __init__.py
      📄 error.py
    📁 routes
      📄 __init__.py
      📄 actions.py
      📄 batches.py
      📄 containers.py
      📄 conversations.py
      📄 embeddings.py
      📄 files.py
      📄 health.py
      📄 images.py
      📄 models.py
      📄 proxy.py
      📄 realtime.py
      📄 register_routes.py
      📄 responses.py
      📄 uploads.py
      📄 vector_stores.py
      📄 videos.py
    📁 utils
      📄 __init__.py
      📄 authy.py
      📄 error_handler.py
      📄 http_client.py
      📄 logger.py
  📁 chatgpt_team_relay.egg-info
    📄 PKG-INFO
    📄 SOURCES.txt
    📄 dependency_links.txt
    📄 requires.txt
    📄 top_level.txt
  📁 data
    📁 conversations
    📁 embeddings
      📄 embeddings.db
    📁 files
      📄 files.db
    📁 images
      📄 images.db
    📁 jobs
      📄 jobs.db
    📁 models
      📄 models.db
      📄 openai_models_categorized.csv
      📄 openai_models_categorized.json
    📁 uploads
      📄 attachments.db
      📄 file_9aa498e1dbb0
    📁 usage
      📄 usage.db
    📁 vector_stores
      📄 vectors.db
    📁 videos
      📄 videos.db
  📁 docs
    📄 README.md
  📁 path
    📁 to
      📄 input.png
  📁 schemas
    📄 __init__.py
    📄 openapi.yaml
  📁 scripts
    📄 README.md
    📄 batch_download_test.sh
    📄 content_endpoints_smoke.sh
    📄 images_variations_smoke.sh
    📄 make_sample_png.py
    📄 make_test_png.py
    📄 openapi_operationid_check.sh
    📄 run_success_gates.sh
    📄 smoke_images_variations.sh
    📄 sse_smoke_test.sh
    📄 test_local.sh
    📄 test_render.sh
    📄 test_success_gates_integration.py
    📄 uploads_e2e_test.sh
  📁 static
    📁 .well-known
      📄 __init__.py
      📄 ai-plugin.json
  📁 tests
    📄 __init__.py
    📄 client.py
    📄 conftest.py
    📄 relay_client_example.py
    📄 test_extended_routes_smoke_integration.py
    📄 test_files_and_batches_integration.py
    📄 test_images_variations_integration.py
    📄 test_local_e2e.py
    📄 test_relay_auth_guard.py
    📄 test_remaining_routes_smoke_integration.py
    📄 test_success_gates_integration.py```

