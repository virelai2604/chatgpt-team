# DefaultApi

All URIs are relative to *https://chatgpt-team.pages.dev*

|Method | HTTP request | Description|
|------------- | ------------- | -------------|
|[**v1AssistantsAssistantIdGet**](#v1assistantsassistantidget) | **GET** /v1/assistants/{assistant_id} | Fetch assistant details|
|[**v1AssistantsPost**](#v1assistantspost) | **POST** /v1/assistants | Create assistant|
|[**v1ChatCompletionsPost**](#v1chatcompletionspost) | **POST** /v1/chat/completions | Modern Chat Completion with tool calling|
|[**v1ModelsGet**](#v1modelsget) | **GET** /v1/models | List available models|
|[**v1ResponsesPost**](#v1responsespost) | **POST** /v1/responses | Streamable response via SSE|
|[**v1ThreadsPost**](#v1threadspost) | **POST** /v1/threads | Start thread|
|[**v1ThreadsThreadIdMessagesPost**](#v1threadsthreadidmessagespost) | **POST** /v1/threads/{thread_id}/messages | Add user message to thread|
|[**v1ThreadsThreadIdRunsPost**](#v1threadsthreadidrunspost) | **POST** /v1/threads/{thread_id}/runs | Start a tool-calling run|
|[**v1ThreadsThreadIdRunsRunIdStepsGet**](#v1threadsthreadidrunsrunidstepsget) | **GET** /v1/threads/{thread_id}/runs/{run_id}/steps | Fetch execution steps|

# **v1AssistantsAssistantIdGet**
> v1AssistantsAssistantIdGet()


### Example

```typescript
import {
    DefaultApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new DefaultApi(configuration);

let assistantId: string; // (default to undefined)

const { status, data } = await apiInstance.v1AssistantsAssistantIdGet(
    assistantId
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **assistantId** | [**string**] |  | defaults to undefined|


### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Assistant info |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **v1AssistantsPost**
> v1AssistantsPost()


### Example

```typescript
import {
    DefaultApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new DefaultApi(configuration);

const { status, data } = await apiInstance.v1AssistantsPost();
```

### Parameters
This endpoint does not have any parameters.


### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Assistant object |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **v1ChatCompletionsPost**
> ChatCompletionResponse v1ChatCompletionsPost(chatCompletionRequest)


### Example

```typescript
import {
    DefaultApi,
    Configuration,
    ChatCompletionRequest
} from './api';

const configuration = new Configuration();
const apiInstance = new DefaultApi(configuration);

let chatCompletionRequest: ChatCompletionRequest; //

const { status, data } = await apiInstance.v1ChatCompletionsPost(
    chatCompletionRequest
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **chatCompletionRequest** | **ChatCompletionRequest**|  | |


### Return type

**ChatCompletionResponse**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Chat result |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **v1ModelsGet**
> v1ModelsGet()


### Example

```typescript
import {
    DefaultApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new DefaultApi(configuration);

const { status, data } = await apiInstance.v1ModelsGet();
```

### Parameters
This endpoint does not have any parameters.


### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Array of model objects |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **v1ResponsesPost**
> v1ResponsesPost(assistantRequest)


### Example

```typescript
import {
    DefaultApi,
    Configuration,
    AssistantRequest
} from './api';

const configuration = new Configuration();
const apiInstance = new DefaultApi(configuration);

let assistantRequest: AssistantRequest; //

const { status, data } = await apiInstance.v1ResponsesPost(
    assistantRequest
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **assistantRequest** | **AssistantRequest**|  | |


### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | SSE or final chat result |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **v1ThreadsPost**
> v1ThreadsPost()


### Example

```typescript
import {
    DefaultApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new DefaultApi(configuration);

const { status, data } = await apiInstance.v1ThreadsPost();
```

### Parameters
This endpoint does not have any parameters.


### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Thread created |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **v1ThreadsThreadIdMessagesPost**
> v1ThreadsThreadIdMessagesPost()


### Example

```typescript
import {
    DefaultApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new DefaultApi(configuration);

let threadId: string; // (default to undefined)

const { status, data } = await apiInstance.v1ThreadsThreadIdMessagesPost(
    threadId
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **threadId** | [**string**] |  | defaults to undefined|


### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Message added |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **v1ThreadsThreadIdRunsPost**
> v1ThreadsThreadIdRunsPost()


### Example

```typescript
import {
    DefaultApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new DefaultApi(configuration);

let threadId: string; // (default to undefined)

const { status, data } = await apiInstance.v1ThreadsThreadIdRunsPost(
    threadId
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **threadId** | [**string**] |  | defaults to undefined|


### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Run started |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **v1ThreadsThreadIdRunsRunIdStepsGet**
> v1ThreadsThreadIdRunsRunIdStepsGet()


### Example

```typescript
import {
    DefaultApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new DefaultApi(configuration);

let threadId: string; // (default to undefined)
let runId: string; // (default to undefined)

const { status, data } = await apiInstance.v1ThreadsThreadIdRunsRunIdStepsGet(
    threadId,
    runId
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **threadId** | [**string**] |  | defaults to undefined|
| **runId** | [**string**] |  | defaults to undefined|


### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Steps array |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

