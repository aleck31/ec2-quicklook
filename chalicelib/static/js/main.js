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
      category: '',
      family: '',
      type: '',
      voltype: 'gp3',
      volsize: 60
    },
    loading: false,
    typeLoading: false,
    validated: false,
    instance: null,
    volume: null,
    previousPrice: null,
    comparisonItems: [],
    highlightedRowIndex: -1, // Track which row to highlight
    regionOptions: [],
    operationOptions: [],
    categoryOptions: [],
    familyOptions: [],
    typeOptions: [],
    voltypeOptions: [],
    detailUrl: null,
    familyState: null,
    familyFeedback: ''
  },
  computed: {
    isButtonDisabled() {
      return !this.form.type || this.loading || this.familyState === false;
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
        { key: 'type', label: 'Instance Type' },
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
            type: this.form.type,
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
        this.detailUrl = `detail?region=${this.form.region}&type=${this.form.type}`;

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
    async updateFamily() {
      // Reset validation state
      this.familyState = null;
      this.familyFeedback = '';
      
      try {
        const response = await axios.get('instance/family', {
          params: {
            region: this.form.region,
            arch: this.form.arch,
            category: this.form.category
          }
        });
        console.log('API Response:', response.data);
        this.familyOptions = response.data.map(item => ({
          value: item.name,
          text: `${item.name}  :  ${item.note}`
        }));
        // Set default family if available
        if (this.familyOptions.length > 0) {
          const defaultFamily = this.familyOptions.find(f => ['m5', 'm6g'].includes(f.value));
          if (defaultFamily) {
            this.form.family = defaultFamily.value;
            this.updateTypes();
          }
        }
      } catch (error) {
        console.error('Error fetching families:', error);
        this.familyState = false;
        this.familyFeedback = 'Failed to load instance families. Please try again.';
      }
    },
    async updateTypes() {
      if (!this.form.family) return;
      
      this.typeLoading = true;
      try {
        // Store current size suffix before updating types
        const currentType = this.form.type;
        const currentSizeSuffix = currentType ? currentType.match(/[a-z]+\d*\.(.+)/)?.[1] : null;

        const response = await axios.get('instance/types', {
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
            const getSizeSuffix = (type) => {
              const match = type.match(/[a-z]+\d*\.(.+)/);
              return match ? match[1] : '';
            };
            
            const sizeA = getSizeSuffix(a.value);
            const sizeB = getSizeSuffix(b.value);
            
            return (sizeOrder[sizeA] || 0) - (sizeOrder[sizeB] || 0);
          });

          // Set instance type with priority:
          // 1. Same size as current (e.g., if current is m5.4xlarge, try to find *.4xlarge)
          // 2. .large instance
          // 3. First available option
          let selectedType;
          if (currentSizeSuffix) {
            selectedType = this.typeOptions.find(t => t.value.endsWith(`.${currentSizeSuffix}`));
          }
          if (!selectedType) {
            selectedType = this.typeOptions.find(t => t.value.endsWith('.large')) || this.typeOptions[0];
          }
          this.form.type = selectedType.value;
          this.familyState = true;
          this.familyFeedback = '';
        } else {
          // Clear type options and show warning when no instance types are available
          this.typeOptions = [{
            value: '',
            text: 'No instance types available',
            disabled: true
          }];
          this.form.type = '';
          this.familyState = false;
          this.familyFeedback = `"${this.form.family}" is not supported in this region.`;
        }
      } catch (error) {
        console.error('Error fetching types:', error);
        this.typeOptions = [{
          value: '',
          text: 'Error loading instance types',
          disabled: true
        }];
        this.form.type = '';
        this.familyState = false;
        this.familyFeedback = 'Failed to load instance types. Please try again.';
      } finally {
        this.typeLoading = false;
      }
    },
    addToComparison() {
      if (!this.instance || this.comparisonItems.length >= 8) return;

      // Check if this instance type is already in the comparison
      const existingIndex = this.comparisonItems.findIndex(item => 
        item.type === this.form.type && 
        item.region === this.form.region
      );
      if (existingIndex >= 0) {
        // Instance type from this region already in comparison, highlight the row
        this.highlightRow(existingIndex);
        return;
      }

      // Add the current instance to the comparison list
      const item = {
        type: this.form.type,
        region: this.form.region,
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
      this.form.category = '';
      this.form.family = '';
      this.form.type = '';
    },
    'form.category'() {
      this.form.family = '';
      this.form.type = '';
      if (this.form.category) {
        this.updateFamily();
      }
    },
    'form.region'() {
      this.updateTypes();
    },
    'form.family'() {
      this.updateTypes();
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

      this.categoryOptions = categoryResponse.data.map(cat => ({
        value: cat.category,
        text: `${cat.display_name}  -  ${cat.description}`
      }));

      // Set default values
      this.form.operation = this.operationOptions.find(op => op.text === 'Linux/UNIX')?.value;
      
      // Set default category to 'compute'
      const defaultCategory = this.categoryOptions.find(cat => cat.value === 'general');
      if (defaultCategory) {
        this.form.category = defaultCategory.value;
        this.updateFamily();
      }

    } catch (error) {
      console.error('Error loading initial data:', error);
    }
  }
});
