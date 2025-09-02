#!/usr/bin/env python3
"""
Download and process comprehensive drug information dataset from Kaggle
for integration with vademecum service
"""

import kagglehub
import pandas as pd
import os
from pathlib import Path
import json

def download_and_process_vademecum():
    """Download comprehensive drug dataset and process for our vademecum service"""
    
    print("💊 Downloading Comprehensive Drug Information Dataset")
    print("=" * 60)
    
    try:
        # Download latest version
        print("📥 Downloading dataset from Kaggle...")
        path = kagglehub.dataset_download("anoopjohny/comprehensive-drug-information-dataset")
        
        print(f"✅ Dataset downloaded to: {path}")
        
        # List all files in the dataset
        dataset_path = Path(path)
        files = list(dataset_path.glob("*"))
        print(f"\n📁 Files in dataset:")
        for file in files:
            file_size = file.stat().st_size / (1024 * 1024)  # MB
            print(f"   - {file.name} ({file_size:.2f} MB)")
        
        # Find and load the main drug dataset
        csv_files = list(dataset_path.glob("*.csv"))
        if csv_files:
            main_file = csv_files[0]  # Use first CSV file
            print(f"\n📊 Loading main dataset: {main_file.name}")
            
            df = pd.read_csv(main_file)
            print(f"   ✅ Loaded {len(df):,} rows × {len(df.columns)} columns")
            print(f"   📋 Columns: {list(df.columns)}")
            
            # Show sample data
            print(f"\n🔍 Sample data:")
            print(df.head())
            
            # Process and clean data for Spanish use
            print(f"\n🧹 Processing data for Spanish pharmacy agent...")
            
            # Map English columns to Spanish field names expected by vademecum_service.py
            column_mapping = {
                'Drug Name': 'nombre',
                'Generic Name': 'principio_activo', 
                'Drug Class': 'categoria',
                'Indications': 'indicaciones',
                'Dosage Form': 'forma',
                'Strength': 'concentracion',
                'Route of Administration': 'via_administracion',
                'Mechanism of Action': 'mecanismo_accion',
                'Side Effects': 'efectos_secundarios',
                'Contraindications': 'contraindicaciones',
                'Interactions': 'interacciones',
                'Warnings and Precautions': 'advertencias',
                'Pregnancy Category': 'categoria_embarazo',
                'Storage Conditions': 'almacenamiento',
                'Manufacturer': 'fabricante',
                'Availability': 'disponibilidad',
                'Price': 'precio'
            }
            
            # Rename columns to Spanish
            df_spanish = df.rename(columns=column_mapping)
            
            # Add safety disclaimers and format for agent use
            df_spanish['advertencias'] = df_spanish['advertencias'].fillna("Consulte con un profesional de la salud antes de usar este medicamento.")
            df_spanish['contraindicaciones_fuente'] = "Fuente: Dataset farmacológico completo - Solo información general"
            df_spanish['presentacion'] = df_spanish['forma'] + " - " + df_spanish['concentracion'].fillna("Ver envase")
            
            # Clean up data
            df_spanish = df_spanish.fillna("")
            
            # Basic data analysis
            print(f"\n📈 Dataset Analysis:")
            print(f"   - Total medications: {len(df_spanish):,}")
            print(f"   - Unique drug names: {df_spanish['nombre'].nunique():,}")
            print(f"   - Entries with indications: {df_spanish['indicaciones'].notna().sum():,}")
            print(f"   - Spanish column mapping completed")
            
            # Save processed data to our data directory
            output_dir = Path("./data")
            output_dir.mkdir(exist_ok=True)
            
            # Save as CSV first (simpler, no dependencies)
            output_file = output_dir / "comprehensive_vademecum.csv"
            df_spanish.to_csv(output_file, index=False, encoding='utf-8')
            print(f"   ✅ Saved processed data to: {output_file}")
            
            # Save sample as JSON for inspection
            sample_file = output_dir / "vademecum_sample.json"
            sample_data = df_spanish.head(10).to_dict('records')
            with open(sample_file, 'w', encoding='utf-8') as f:
                json.dump(sample_data, f, indent=2, ensure_ascii=False)
            print(f"   ✅ Saved sample data to: {sample_file}")
            
            # Update our environment to use this dataset
            env_file = Path(".env")
            if env_file.exists():
                env_content = env_file.read_text()
                if "VADEMECUM_PATH" in env_content:
                    # Update the path in .env
                    updated_content = env_content.replace(
                        'VADEMECUM_PATH="./data/vademecum_clean.parquet"',
                        f'VADEMECUM_PATH="./data/comprehensive_vademecum.csv"'
                    )
                    env_file.write_text(updated_content)
                    print(f"   ✅ Updated .env to use new dataset")
            
            return {
                "success": True,
                "dataset_path": str(output_file),
                "total_medications": len(df_spanish),
                "columns": list(df_spanish.columns),
                "sample_data": sample_data[:3]
            }
        
        else:
            print("❌ No CSV files found in dataset")
            return {"success": False, "error": "No CSV files found"}
            
    except Exception as e:
        print(f"❌ Error downloading/processing dataset: {e}")
        return {"success": False, "error": str(e)}

def test_vademecum_integration():
    """Test the integration with our existing vademecum service"""
    
    print("\n🧪 Testing vademecum service integration...")
    
    try:
        from app.services.vademecum_service import load_vademecum, search_vademecum
        
        # Load the new dataset
        vademecum_path = "./data/comprehensive_vademecum.csv"
        if os.path.exists(vademecum_path):
            items = load_vademecum(vademecum_path)
            print(f"   ✅ Loaded {len(items):,} medications into vademecum service")
            
            # Test search functionality with both English and Spanish terms
            test_searches = ["aspirin", "aspirina", "paracetamol", "acetaminophen", "ibuprofen", "amoxicillin"]
            
            for query in test_searches:
                results = search_vademecum(items, query, limit=3)
                print(f"   🔍 Search '{query}': {len(results)} results")
                if results:
                    result = results[0]
                    print(f"      📋 {result.get('nombre', 'Unknown')} - {result.get('principio_activo', 'N/A')}")
                    print(f"      💊 Forma: {result.get('forma', 'N/A')} | Concentración: {result.get('concentracion', 'N/A')}")
            
            return True
        else:
            print(f"   ❌ Dataset not found at {vademecum_path}")
            return False
            
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    # Download and process dataset
    result = download_and_process_vademecum()
    
    if result["success"]:
        print(f"\n✅ Dataset successfully integrated!")
        print(f"📊 {result['total_medications']:,} medications available")
        print(f"📋 Columns: {', '.join(result['columns'])}")
        
        # Test integration
        test_vademecum_integration()
        
        print(f"\n🚀 Ready for AI agent integration!")
        print(f"💡 The agent can now provide information about {result['total_medications']:,} medications")
        
    else:
        print(f"\n❌ Dataset integration failed: {result['error']}")
