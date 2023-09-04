package com.example.smartaccess

import android.app.Activity
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.drawable.BitmapDrawable
import android.os.Bundle
import android.provider.MediaStore
import android.util.Base64
import android.util.Log
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.ImageView
import android.widget.ProgressBar
import androidx.activity.result.ActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import com.google.firebase.FirebaseApp
import com.google.firebase.database.DataSnapshot
import com.google.firebase.database.DatabaseError
import com.google.firebase.database.DatabaseReference
import com.google.firebase.database.FirebaseDatabase
import com.google.firebase.database.ValueEventListener
import okhttp3.*
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.POST
import java.io.ByteArrayOutputStream
import android.widget.Toast


class MainActivity : AppCompatActivity() {


    val url = "http://192.168.164.12:8000"
    var imageBitMapSend = ""

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        FirebaseApp.initializeApp(this);
        val mDatabase: DatabaseReference = FirebaseDatabase.getInstance().reference

        mDatabase.child("license_plate").addValueEventListener(object : ValueEventListener {
            override fun onDataChange(dataSnapshot: DataSnapshot) {
                // Obtener datos del dataSnapshot
                val license_plate = dataSnapshot.getValue(String::class.java).toString()
                findViewById<EditText>(R.id.editTextPlaca).setText(license_plate)
            }

            override fun onCancelled(databaseError: DatabaseError) {
                // Tratar posibles errores aquí
            }
        })


        setContentView(R.layout.activity_main)

        val btnCamara = findViewById<Button>(R.id.btnCamara)
        val btnCamara_send = findViewById<Button>(R.id.btnCamara2)
        val btnCamara_save = findViewById<Button>(R.id.buttonSave)
        findViewById<ProgressBar>(R.id.progressBar).visibility = View.GONE

        findViewById<EditText>(R.id.editTextPlaca).setText("")

        //Evento al presionar el botón
        btnCamara.setOnClickListener {
            findViewById<EditText>(R.id.editTextCedula).setText("")
            findViewById<EditText>(R.id.editTextName).setText("")

            startForResult.launch(Intent(MediaStore.ACTION_IMAGE_CAPTURE))
        }
        btnCamara_send.setOnClickListener{
            sendImageToAPI()
        }

        btnCamara_save.setOnClickListener{
            saveData()
        }
    }

    private val startForResult = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result: ActivityResult ->
            if (result.resultCode == Activity.RESULT_OK) {
                val intent = result.data
                val imageBitmap = intent?.extras?.get("data") as Bitmap
                val imageView = findViewById<ImageView>(R.id.imageView)
                imageBitMapSend  = bitmapToBase64(imageBitmap)
                imageView.setImageBitmap(imageBitmap)
            }
        }

    fun bitmapToBase64(bitmap: Bitmap): String {
        val byteArrayOutputStream = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG, 100, byteArrayOutputStream)
        val byteArray = byteArrayOutputStream.toByteArray()
        return Base64.encodeToString(byteArray, Base64.DEFAULT)
    }

    private fun sendImageToAPI(){
        findViewById<ProgressBar>(R.id.progressBar).visibility = View.VISIBLE
        val imageView = findViewById<ImageView>(R.id.imageView)
        val bitmap: Bitmap? = (imageView.drawable as? BitmapDrawable)?.bitmap

        // Verificar si se obtuvo el Bitmap y hacer algo con él
        if (bitmap != null) {
            makePostRequestRetrofit(url, imageBitMapSend)
        }
    }

    data class UserRequestBody(
        val image: String
    )

    data class UserResponse(
        val name: String,
        val ci: String
    )

    interface ApiService {
        @POST("/getInformationUser")
        fun generateInformationByUser(@Body data: UserRequestBody): Call<UserResponse>
    }

    private fun makePostRequestRetrofit(url: String, imageBase64String: String){
        val retrofit: Retrofit = Retrofit.Builder()
            .baseUrl(url) // For local emulator. Replace "YOUR_PORT" with your API's port.
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        val apiService: ApiService = retrofit.create(ApiService::class.java)
        val requestBody = UserRequestBody(imageBase64String) // Where imageBase64String is your image in base64 format
        val call: Call<UserResponse> = apiService.generateInformationByUser(requestBody)
        Toast.makeText(this, "Espere un momento hasta que se complete la solicitud", Toast.LENGTH_SHORT).show()

        call.enqueue(object : Callback<UserResponse> {
            override fun onResponse(call: Call<UserResponse>, response: Response<UserResponse>) {
                findViewById<ProgressBar>(R.id.progressBar).visibility = View.GONE

                if (response.isSuccessful) {
                    val userInfo = response.body()
                    findViewById<EditText>(R.id.editTextCedula).setText(userInfo?.ci.toString())
                    findViewById<EditText>(R.id.editTextName).setText(userInfo?.name.toString())

                } else {

                    Log.e("RetrofitError", "HTTP error code: ${response.code()}")
                    Log.e("RetrofitError", "Error body: ${response.errorBody()?.string()}")
                }
            }

            override fun onFailure(call: Call<UserResponse>, t: Throwable) {
                Log.e("RetrofitError", "Network or serialization error", t)
            }
        })

    }

    private fun saveData(){
        val license = findViewById<EditText>(R.id.editTextPlaca)
        val ni = findViewById<EditText>(R.id.editTextCedula)
        val name = findViewById<EditText>(R.id.editTextName)

        val mDatabase: DatabaseReference = FirebaseDatabase.getInstance().reference

        val data: Map<String, Any> = mapOf(
            "name" to name.text.toString(),
            "ni" to ni.text.toString(),
            "license" to license.text.toString()
        )
        val key = mDatabase.child("generic").push().key // Generates a unique key

        if (name.text.toString() !== "" && ni.text.toString() !== "" && license.text.toString() !== ""){
            mDatabase.child("users_register").child(key.toString()).setValue(data)
                .addOnCompleteListener {
                    if (it.isSuccessful) {
                        Toast.makeText(this, "¡Usuario registrado correctamente!", Toast.LENGTH_SHORT).show()
                        license.setText("")
                        ni.setText("")
                        name.setText("")

                    } else {
                        Toast.makeText(this, "¡Error al guardar usuario!", Toast.LENGTH_SHORT).show()
                    }
                }
        } else {
            Toast.makeText(this, "¡Llene todos los campos!", Toast.LENGTH_SHORT).show()

        }


    }

//    private fun makePostRequest(url: String, requestBody: JSONObject) {
//        val client = OkHttpClient()
//        val mediaType = "application/json; charset=utf-8".toMediaTypeOrNull()
//
//        val request = Request.Builder()
//            .url(url)
//            .post(RequestBody.create(mediaType, requestBody.toString()))
//            .build()
//
//        println("pst al request $request")
//
//        client.newCall(request).enqueue(object : Callback {
//            override fun onFailure(call: Call, e: IOException) {}
//
//            override fun onResponse(call: Call, response: Response) {
//                val responseData = response.body?.string().toString()
//                val json = JsonParser.parseString(responseData).asJsonObject
//                println(json)
////                runOnUiThread {
////                    if (json.has("generated_text")){
////                        val regex = Regex("[^a-zA-Z0-9]")
////                        findViewById<TextView>(R.id.placaView).text = json.get("generated_text").toString().replace(regex, "").replace(Regex("(\\D)(\\d+)"), "$1-$2")
////                    }
////                    Log.e("response", json.toString())
////                }
//            }
//        })
//    }

}