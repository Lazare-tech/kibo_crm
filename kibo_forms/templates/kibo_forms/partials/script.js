{% comment %} function onSubmit(e) {
  // L'URL de ton tunnel ngrok (vérifie bien que l'ID 549a... est toujours le même)
  var url = "https://974b-197-239-108-194.ngrok-free.app/forms/webhook/evaluation_securite_informatique/";
  
  var formResponse = e.response;
  var itemResponses = formResponse.getItemResponses();
  var payload = {};

  for (var i = 0; i < itemResponses.length; i++) {
    var itemResponse = itemResponses[i];
    var title = itemResponse.getItem().getTitle();
    var response = itemResponse.getResponse();
    var itemType = itemResponse.getItem().getType();

    // 1. GESTION DES FICHIERS (FILE UPLOAD)
    if (itemType == FormApp.ItemType.FILE_UPLOAD) {
      if (response && response.length > 0) {
        // On transforme les IDs Google Drive en liens réels cliquables
        var fileUrls = response.map(function(fileId) {
          return "https://drive.google.com/open?id=" + fileId;
        });
        payload[title] = fileUrls; 
      } else {
        payload[title] = "Aucun fichier";
      }
    } 
    // 2. GESTION DES CASES À COCHER (CHECKBOX)
    // Google envoie déjà un tableau [A, B], le JSONField de Django l'adorera
    else {
      payload[title] = response;
    }
  }

  // Ajout de métadonnées utiles (Optionnel)
  payload["_submitted_at"] = String(formResponse.getTimestamp().toISOString());
  payload["_user_email"] = formResponse.getRespondentEmail() || "";

  var options = {
    "method": "post",
    "contentType": "application/json",
    "payload": JSON.stringify(payload),
    "muteHttpExceptions": true // Pour éviter que le script s'arrête si Django est éteint
  };

  try {
    var result = UrlFetchApp.fetch(url, options);
    Logger.log("Réponse Django : " + result.getContentText());
  } catch (error) {
    Logger.log("Erreur d'envoi : " + error.toString());
  } {% endcomment %}
