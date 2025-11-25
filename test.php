<?php
// Paramètres de connexion
$host = "192.168.56.20";   // IP de ta VM MariaDB
$user = "vagrant";         // utilisateur créé
$password = "vagrant";     // mot de passe
$dbname = "vagrant";       // base de données

// Connexion
$conn = new mysqli($host, $user, $password, $dbname);

// Vérifier la connexion
if ($conn->connect_error) {
    die("Connexion échouée: " . $conn->connect_error);
}

// Créer la table si elle n'existe pas
$sql = "CREATE TABLE IF NOT EXISTS plus_jolie_femme (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4";

if ($conn->query($sql) === TRUE) {
    echo "Table créée ou déjà existante.<br>";
} else {
    echo "Erreur création table: " . $conn->error;
}

// Insérer des données
$femmes = ["Zendaya", "Margot Robbie", "Ana de Armas", "Gal Gadot", "Emma Watson"];

foreach ($femmes as $nom) {
    $stmt = $conn->prepare("INSERT INTO plus_jolie_femme (nom) VALUES (?)");
    $stmt->bind_param("s", $nom);
    $stmt->execute();
    $stmt->close();
}

echo "Insertion terminée. Voici quelques unes des futur ex de kevin ! lol .<br>";

// Afficher les données
$result = $conn->query("SELECT * FROM plus_jolie_femme");
while ($row = $result->fetch_assoc()) {
    echo $row['id'] . " - " . $row['nom'] . "<br>";
}

$conn->close();
?>
