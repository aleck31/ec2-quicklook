console.log('Loading modular main.js...');

new Vue({
  el: '#app',
  delimiters: ['[[', ']]'],  // Set delimiters for this instance
  mounted() {
    // Remove v-cloak after Vue is mounted
    this.$el.removeAttribute('v-cloak');
  },
  data: {
    form: {
      region: 'us-east-1',
      arch: 'x86_64',
      operation: '',
      family: '',
      size: '',
      voltype: 'gp3',
      volsize: 60
    },
    loading: false,
    familyLoading: false,
    sizesLoading: false,
    validated: false,
    instance: null,
    volume: null,
    previousPrice: null,
    comparisonItems: [],
    highlightedRowIndex: -1, // Track which row to highlight
    regionOptions: [],
    operationOptions: [],
    categoryOptions: [], // Keep for grouping
    familyOptions: [], // Store all families for current architecture
    typeOptions: [],
    voltypeOptions: [],
    detailUrl: null,
    familyState: null,
    familyFeedback: ''
  },
  computed: {
    groupedFamilyOptions() {
      // Group families by category
      const groups = [];
      
      // Create a map to group families by category
      const categoryGroups = {};
      
      this.familyOptions.forEach(family => {
        if (!categoryGroups[family.category]) {
          // Find the category info from categoryOptions
          const categoryInfo = this.categoryOptions.find(c => c.category === family.category);
          if (categoryInfo) {
            categoryGroups[family.category] = {
              label: `${categoryInfo.display_name} - ${categoryInfo.description}`,
              options: []
            };
          }
        }
        
        if (categoryGroups[family.category]) {
          categoryGroups[family.category].options.push({
            value: family.name,
            text: `${family.name} \u0020 | \u0020 ${family.note}`
          });
        }
      });
      
      // Convert to array and sort options within each group
      Object.values(categoryGroups).forEach(group => {
        if (group.options.length > 0) {
          // Sort options by family name
          group.options.sort((a, b) => a.value.localeCompare(b.value));
          groups.push(group);
        }
      });
      
      return groups;
    },
    
    isButtonDisabled() {
      return !this.form.size || this.loading || this.familyState === false;
    },
    priceChange() {
      if (!this.instance || !this.previousPrice) return null;
      const currentPrice = this.instance.listPrice.pricePerUnit.value;
      const change = ((currentPrice - this.previousPrice) / this.previousPrice) * 100;
      return change;
    },
    canCompare() {
      return this.instance && this.comparisonItems.length < 8;
    },
    hardwareItems() {
      return this.instance ? Object.entries(this.instance.hardwareSpecs)
        .filter(([_, value]) => value !== null && value !== undefined && value !== '') // Filter out any empty entries
        .map(([key, value]) => ({
          key,
          value
        })) : [];
    },
    softwareItems() {
      return this.instance ? Object.entries(this.instance.softwareSpecs).map(([key, value]) => ({
        key,
        value
      })) : [];
    },
    featureItems() {
      return this.instance ? Object.entries(this.instance.productFeature).map(([key, value]) => ({
        key,
        value
      })) : [];
    },
    storageItems() {
      return this.instance ? Object.entries(this.instance.instanceStorage).map(([key, value]) => ({
        key,
        value
      })) : [];
    },
    volumeItems() {
      return this.volume ? Object.entries(this.volume.productSpecs).map(([key, value]) => ({
        key,
        value
      })) : [];
    },
    comparisonFields() {
      return [
        { key: 'region', label: 'Region' },
        { key: 'size', label: 'Instance Size' },
        { key: 'price', label: 'Price (Month)' },
        { key: 'vcpu', label: 'Processor' },
        { key: 'memory', label: 'Memory' },
        { key: 'network', label: 'Network Performance' },
        { key: 'actions', label: '' }
      ];
    }
  },
  methods: {
    async quickLook() {
      this.loading = true;
      try {
        // Store previous price for comparison
        this.previousPrice = this.instance?.listPrice.pricePerUnit.value;

        // Query instance data
        const instanceResponse = await axios.get('product/instance', {
          params: {
            region: this.form.region,
            typesize: this.form.size,
            op: this.form.operation
          }
        });
        this.instance = instanceResponse.data;

        // Query volume data
        const volumeResponse = await axios.get('product/volume', {
          params: {
            region: this.form.region,
            type: this.form.voltype,
            size: this.form.volsize
          }
        });
        this.volume = volumeResponse.data;

        // Update detail URL
        this.detailUrl = `detail?region=${this.form.region}&type=${this.form.size}`;

      } catch (error) {
        console.error('Error fetching data:', error);
        this.$bvToast.toast('Failed to fetch data. Please try again.', {
          title: 'Error',
          variant: 'danger',
          solid: true
        });
      } finally {
        this.loading = false;
      }
    },

    async updateFamilyList() {
      this.familyLoading = true;
      try {
        // Get families for current architecture
        const response = await axios.get('instance/family', {
          params: {
            region: 'us-east-1', // Reference region to get all families
            arch: this.form.arch
          }
        });

        // Store all families with their metadata
        this.familyOptions = response.data;
        console.log('Loaded instances types for architecture:', this.familyOptions.length);
        
        // Set default family if none selected
        if (!this.form.family) {
          this.setDefaultFamily();
        } else {
          // Update sizes for current family
          await this.updateSizes();
        }
      } catch (error) {
        console.error('Error loading families:', error);
        this.familyOptions = [];
        this.familyState = false;
        this.familyFeedback = 'Failed to load instance families. Please try again.';
      } finally {
        this.familyLoading = false;
      }
    },

    setDefaultFamily() {
      // Clear current selection
      this.form.family = '';
      this.form.size = '';

      // Find available default family based on architecture
      const archDefaults = this.form.arch === 'arm64' ? 
        ['m7g', 'm8g', 'm7g'] : // ARM defaults
        ['m6i', 'm7i', 'm5']; // x86 defaults
      
      // Try each default family in order
      let selectedFamily = null;
      for (const defaultFamily of archDefaults) {
        const found = this.familyOptions.find(f => f.name === defaultFamily);
        if (found) {
          selectedFamily = found;
          break;
        }
      }

      // If no default family is found, pick first family
      if (!selectedFamily && this.familyOptions.length > 0) {
        selectedFamily = this.familyOptions[0];
      }

      // Set the selected family and update types
      if (selectedFamily) {
        this.form.family = selectedFamily.name;
        this.updateSizes();
      }
    },

    async updateSizes() {
      if (!this.form.family) return;

      this.sizesLoading = true;
      try {
        // Store current size suffix before updating size list
        const currentSize = this.form.size;
        const currentSizeSuffix = currentSize ? currentSize.match(/[a-z]+\d*\.(.+)/)?.[1] : null;

        const response = await axios.get('instance/sizes', {
          params: {
            region: this.form.region,
            arch: this.form.arch,
            family: this.form.family
          }
        });

        if (response.data && response.data.length > 0) {
          this.typeOptions = response.data.map(item => ({
            value: item.instanceType,
            text: item.instanceType
          }));
          // Sort instance types by size
          this.typeOptions.sort((a, b) => {
            // Define size order mapping
            const sizeOrder = {
              'nano': 1, 'micro': 2, 'small': 3, 'medium': 4, 'large': 5,
              'xlarge': 6, '2xlarge': 7, '3xlarge': 8, '4xlarge': 9,
              '6xlarge': 10, '8xlarge': 11, '9xlarge': 12, '10xlarge': 13,
              '12xlarge': 14, '16xlarge': 15, '18xlarge': 16, '24xlarge': 17,
              '32xlarge': 18, '48xlarge': 19, 'metal': 20
            };
            
            // Extract size suffix (e.g., 'large', 'xlarge', '2xlarge')
            const getSizeSuffix = (size) => {
              const match = size.match(/[a-z]+\d*\.(.+)/);
              return match ? match[1] : '';
            };
            
            const sizeA = getSizeSuffix(a.value);
            const sizeB = getSizeSuffix(b.value);
            
            return (sizeOrder[sizeA] || 0) - (sizeOrder[sizeB] || 0);
          });

          // Set instance size with priority:
          // 1. Same size as current (e.g., if current is m5.4xlarge, try to find *.4xlarge)
          // 2. .large instance
          // 3. First available option
          let selectedSize;
          if (currentSizeSuffix) {
            selectedSize = this.typeOptions.find(t => t.value.endsWith(`.${currentSizeSuffix}`));
          }
          if (!selectedSize) {
            selectedSize = this.typeOptions.find(t => t.value.endsWith('.large')) || this.typeOptions[0];
          }
          this.form.size = selectedSize.value;
          this.familyState = true;
          this.familyFeedback = '';
        } else {
          // Clear size options and show warning when no instance types are available
          this.typeOptions = [{
            value: '',
            text: 'No instance available',
            disabled: true
          }];
          this.form.size = '';
          this.familyState = false;
          this.familyFeedback = `The "${this.form.family}" instance is not available in ${this.form.region}.`;
        }
      } catch (error) {
        console.error('Error fetching types:', error);
        this.typeOptions = [{
          value: '',
          text: 'Error loading instance types',
          disabled: true
        }];
        this.form.size = '';
        this.familyState = false;
        this.familyFeedback = 'Failed to load instance types. Please try again.';
      } finally {
        this.sizesLoading = false;
      }
    },
    addToComparison() {
      if (!this.instance || this.comparisonItems.length >= 8) return;

      // Check if this instance size is already in the comparison
      const existingIndex = this.comparisonItems.findIndex(item => 
        item.size === this.form.size && 
        item.region === this.form.region
      );
      if (existingIndex >= 0) {
        // Instance size from this region already in comparison, highlight the row
        this.highlightRow(existingIndex);
        return;
      }

      // Add the current instance to the comparison list
      const item = {
        region: this.form.region,
        size: this.form.size,
        price: `${this.instance.listPrice.pricePerUnit.currency} ${this.instance.listPrice.pricePerUnit.value.toFixed(2)}`,
        vcpu: `${this.instance.hardwareSpecs.physicalProcessor} ${this.instance.hardwareSpecs.clockSpeed}`,
        memory: this.instance.hardwareSpecs.memory,
        network: this.instance.hardwareSpecs.networkPerformance,
        _rowVariant: '' // Default no highlight
      };

      this.comparisonItems.push(item);
    },
    
    highlightRow(index) {
      // Set the row variant to warning (yellow highlight)
      this.$set(this.comparisonItems[index], '_rowVariant', 'warning');
      
      // Reset the highlight after a short delay
      setTimeout(() => {
        if (this.comparisonItems[index]) {
          this.$set(this.comparisonItems[index], '_rowVariant', '');
        }
      }, 2000);
    },
    
    removeFromComparison(index) {
      if (index >= 0 && index < this.comparisonItems.length) {
        this.comparisonItems.splice(index, 1);
      }
    }
  },
  watch: {
    'form.arch'() {
      // When architecture changes, clear current selection and update family list
      this.form.family = '';
      this.form.size = '';
      this.familyState = null;
      this.familyFeedback = '';
      this.updateFamilyList();
    },
    'form.region'() {
      // When region changes, update sizes to check availability
      if (this.form.family) {
        this.updateSizes();
      }
    },
    'form.family'() {
      // When family changes, update instance types
      if (this.form.family) {
        this.updateSizes();
      }
    }
  },
  async created() {
    try {
      // Load initial data
      const [regionResponse, operationResponse, voltypeResponse, categoryResponse] = await Promise.all([
        axios.get('instance/regions'),
        axios.get('instance/operations'),
        axios.get('instance/voltypes'),
        axios.get('instance/categories')
      ]);

      this.regionOptions = regionResponse.data.map(region => ({
        value: region.code,
        text: `${region.code} ${region.name}`
      }));

      this.operationOptions = operationResponse.data.map(op => ({
        value: op.operation,
        text: op.platform
      }));

      this.voltypeOptions = voltypeResponse.data.map(vt => ({
        value: vt,
        text: vt
      }));

      this.categoryOptions = categoryResponse.data;

      // Set default operation
      this.form.operation = this.operationOptions.find(op => op.text === 'Linux/UNIX')?.value;

      // Load families for initial architecture
      await this.updateFamilyList();

    } catch (error) {
      console.error('Error loading initial data:', error);
    }
  }
});
