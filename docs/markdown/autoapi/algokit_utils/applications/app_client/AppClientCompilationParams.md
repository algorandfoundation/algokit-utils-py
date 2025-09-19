# algokit_utils.applications.app_client.AppClientCompilationParams

#### *class* algokit_utils.applications.app_client.AppClientCompilationParams

Bases: `TypedDict`

Parameters for compiling an application’s TEAL code.

* **Variables:**
  * **deploy_time_params** – Optional template parameters to use during compilation
  * **updatable** – Optional flag indicating if app should be updatable
  * **deletable** – Optional flag indicating if app should be deletable

#### deploy_time_params *: algokit_utils.models.state.TealTemplateParams | None*

#### updatable *: bool | None*

#### deletable *: bool | None*
